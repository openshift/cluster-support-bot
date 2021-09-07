import unittest
from unittest.mock import Mock, patch, call, ANY

from prometheus_client import Counter
from cluster_support_bot.hydra import Client
from cluster_support_bot import messages

mocked_bot_id = 'baz'
mocked_environ = {
    'TELEMETRY_URI': 'https://foo.bar',
    'TELEMETRY_TOKEN': 'deadbeef',
    'BOT_ID': mocked_bot_id,
    'HYDRA_USER': 'averagejoe',
    'HYDRA_PASSWORD': 'hunter2',
    'DASHBOARDS': '',
}
valid_uuid = "644a03cc-3c66-4cdc-9eb4-f430c1ae4359"
invalid_uuid = "0000-0000-00-0000-000000000000"


def setUp(self):
    messages.hydra_client = Mock(spec=Client)
    messages.mention_counter = Mock(spec=Counter)

    self.web_client = Mock()
    self.payload_channel_level_message = {
        'web_client': self.web_client,
        'data': {
            'channel': '#foo',
            'ts': 'bar',
        }
    }
    self.payload_thread_message = {
        'web_client': self.web_client,
        'data': {
            'channel': '#foo',
            'ts': 'bar',
            'thread_ts': 'bar',
        }
    }


@patch.dict('os.environ', mocked_environ)
class TestMiscMessages(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        setUp(self)

    def test_handle_uuid_mention(self):
        params = [
          ["foo", None],
          [valid_uuid, valid_uuid],
          [f"foo {valid_uuid}", valid_uuid],
          [f"{valid_uuid} bar", valid_uuid],
          [f"foo {invalid_uuid} bar", None],
        ]
        for i in params:
            with self.subTest(i=i):
                self.assertEqual(messages.handle_uuid_mention(i[0]), i[1])

        # Metrics
        mention_counter_calls_counter = len([x for x in params if x[1] == valid_uuid])
        expectedmention_counter_calls = mention_counter_calls_counter * [call.labels(valid_uuid)]
        self.assertEqual(messages.mention_counter.method_calls, expectedmention_counter_calls)

    def test_help(self):
        params = [
          self.payload_channel_level_message,
          self.payload_thread_message,
        ]
        for i in params:
            with self.subTest(i=i):
                messages.handle_help(i)
                self.web_client.chat_postMessage.assert_called_once()
                self.web_client.reset_mock()

    def test_handle_parse_args_error(self):
        params = [
          (self.payload_channel_level_message,
           ValueError(), None),
          (self.payload_channel_level_message,
           ValueError({"args": ['foo']}), None),
          (self.payload_channel_level_message,
           ValueError({"args": ['foo'], "message": 'bar'}), True),
        ]
        for i in params:
            with self.subTest(i=i):
                call = messages.handle_parse_args_error(i[0], i[1])
                if not i[2]:
                    self.assertEqual(call, i[2])
                else:
                    self.web_client.chat_postMessage.assert_called_once()
                    self.web_client.reset_mock()


def mocked_get_summary(cluster):
    if cluster == valid_uuid:
        summary = Mock()
        summary.subject = "foo"
        summary.body = "bar"
        return ["info"], [summary], None
    else:
        raise Exception("no such cluster")


def mocked_chat_postMessage(*args, **kwargs):
    r = Mock()
    r.ok = True
    return r


class TestMessages(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUp(self):
        setUp(self)
        messages.get_summary = mocked_get_summary

    async def test_no_response(self):
        params = [
            "hi there",
            f"<@{mocked_bot_id}> hello",
            f"<@{mocked_bot_id}> detail {invalid_uuid}",
        ]
        for i in params:
            with self.subTest(i=i):
                payload = self.payload_channel_level_message.copy()
                payload['data']['text'] = i
                await messages._handle_message("bazbar", payload)
                self.web_client.chat_postMessage.assert_not_called()
                self.assertCountEqual(messages.mention_counter.method_calls, [])
                messages.mention_counter.reset_mock()

    async def test_handle_detail(self):
        # self.web_client.chat_postMessage = mocked_chat_postMessage
        payload = self.payload_channel_level_message.copy()
        payload['data']['text'] = f"<@{mocked_bot_id}> detail {valid_uuid}"
        with patch.dict('os.environ', mocked_environ):
            await messages._handle_message("bazbar", payload)
            self.web_client.chat_postMessage.assert_called_with(
                channel='#foo', thread_ts='bar',
                blocks=[
                    {'type': 'section', 'text': {'type': 'mrkdwn', 'text': 'info'}},
                    # TODO: Fix ANY here with correct summary text
                    {'type': 'section', 'text': {'type': 'mrkdwn', 'text': ANY}}
                ]
            )
            self.assertCountEqual(messages.mention_counter.method_calls, [
                call.labels(valid_uuid)
            ])
            messages.mention_counter.reset_mock()

    async def test_invalid_command(self):
        payload = self.payload_channel_level_message.copy()
        payload['data']['text'] = f"<@{mocked_bot_id}> ping {valid_uuid}"
        with patch.dict('os.environ', mocked_environ):
            await messages._handle_message("bazbar", payload)
            # TODO: Check that help message is printed here
            self.web_client.chat_postMessage.assert_called_once()
            self.assertCountEqual(messages.mention_counter.method_calls, [
                call.labels(valid_uuid)
            ])
            messages.mention_counter.reset_mock()


if __name__ == '__main__':
    unittest.main()
