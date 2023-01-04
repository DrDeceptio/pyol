import asyncio
import datetime
import unittest

from pyol.lib.aio import Scheduler
from pyol.lib.msg import (
    Channel, CmdMsg, Consumer, DataMsg, DeadLetterMsg, EventMsg, MsgBroker,
    MsgIntent, Producer, WiretapMsg,
)


class CmdMsgTestCase(unittest.TestCase):
    def test__init__(self):
        msg = CmdMsg(
            sender='sender',
            headers={'DEAD': 'CODE', 'corr_id': 1234},
            cmd='test',
            cmd_args={'abc': 123, 'def': 456}
        )
        self.assertEqual(msg.intent, MsgIntent.CMD)
        self.assertEqual(msg.sender, 'sender')
        self.assertEqual(msg.headers, {'DEAD': 'CODE', 'corr_id': 1234})
        self.assertEqual(msg.cmd, 'test')
        self.assertEqual(msg.cmd_args, {'abc': 123, 'def': 456})


class DataMsgTestCase(unittest.TestCase):
    def test__init__(self):
        msg = DataMsg(
            sender='sender',
            headers={'DEAD': 'CODE', 'corr_id': 1234},
            data=(b'\xDE\xAD', b'\xC0\xDE')
        )
        self.assertEqual(msg.intent, MsgIntent.DATA)
        self.assertEqual(msg.sender, 'sender')
        self.assertEqual(msg.headers, {'DEAD': 'CODE', 'corr_id': 1234})
        self.assertEqual(msg.data, (b'\xDE\xAD', b'\xC0\xDE'))


class EventMsgTestCase(unittest.TestCase):
    def test__init__(self):
        msg = EventMsg(
            sender='sender',
            headers={'DEAD': 'CODE', 'corr_id': 1234},
            event='test_event',
            data=(1234, 5678)
        )
        self.assertEqual(msg.intent, MsgIntent.EVENT)
        self.assertEqual(msg.sender, 'sender')
        self.assertEqual(msg.headers, {'DEAD': 'CODE', 'corr_id': 1234})
        self.assertEqual(msg.event, 'test_event')
        self.assertEqual(msg.data, (1234, 5678))


class DeadLetterMsgTestCase(unittest.TestCase):
    def test__init__(self):
        orig_msg = DataMsg(sender='sender', headers=None, data=None)
        msg = DeadLetterMsg(channel_name='dead', msg=orig_msg)
        self.assertEqual(msg.intent, MsgIntent.DEADLETTER)
        self.assertEqual(msg.sender, 'deadletter')
        self.assertEqual(msg.headers, {})
        self.assertEqual(msg.channel_name, 'dead')
        self.assertEqual(msg.msg, orig_msg)


class WiretapMsgTestCase(unittest.IsolatedAsyncioTestCase):
    def test__init__(self):
        channel = MsgBroker(Scheduler.build()).add_channel('wiretap_test')
        orig_msg = DataMsg(sender='sender', headers=None, data=None)
        msg = WiretapMsg(channel=channel, msg=orig_msg)

        self.assertEqual(msg.intent, MsgIntent.WIRETAP)
        self.assertEqual(msg.sender, 'wiretap')
        self.assertEqual(msg.headers, {})
        self.assertEqual(msg.channel, channel)
        self.assertEqual(msg.msg, orig_msg)


class ChannelTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.broker = MsgBroker(Scheduler.build())

    def test__init__(self):
        channel = Channel(name='test', broker=self.broker)
        self.assertEqual(channel.name, 'test')
        self.assertEqual(channel.broker, self.broker)
        self.assertEqual(channel.consumers, [])
        self.assertEqual(channel.producers, [])

    def test_register_producer(self):
        channel = Channel(name='test', broker=self.broker)
        producer = Producer(channel=channel)

        channel.register_producer(producer)
        self.assertEqual(channel.producers, [producer])
        channel.register_producer(producer)
        self.assertEqual(channel.producers, [producer])

    def test_deregister_producer(self):
        channel = Channel(name='test', broker=self.broker)
        producer = Producer(channel=channel)
        channel.register_producer(producer)

        channel.deregister_producer(producer)
        self.assertEqual(channel.producers, [])
        channel.deregister_producer(producer)
        self.assertEqual(channel.producers, [])

    def test_register_consumer(self):
        channel = Channel(name='test', broker=self.broker)
        consumer = Consumer(channel=channel)

        channel.register_consumer(consumer)
        self.assertEqual(channel.consumers, [consumer])
        channel.register_consumer(consumer)
        self.assertEqual(channel.consumers, [consumer])

    def test_deregister_consumer(self):
        channel = Channel(name='test', broker=self.broker)
        consumer = Consumer(channel=channel)
        channel.register_consumer(consumer)

        channel.deregister_consumer(consumer)
        self.assertEqual(channel.consumers, [])
        channel.deregister_consumer(consumer)
        self.assertEqual(channel.consumers, [])


class ProducerTestCase(unittest.IsolatedAsyncioTestCase):
    def test__init__(self):
        channel = MsgBroker(Scheduler.build()).add_channel('test__init__')

        producer = Producer(channel=channel)
        self.assertEqual(producer.channel, channel)
        self.assertEqual(producer.registered, False)

    def test_register(self):
        channel = MsgBroker(Scheduler.build()).add_channel('test_register')
        producer = Producer(channel=channel)

        producer.register()
        self.assertTrue(channel.producers, [producer])
        producer.register()
        self.assertTrue(channel.producers, [producer])

    def test_deregister(self):
        channel = MsgBroker(Scheduler.build()).add_channel('test_deregister')
        producer = Producer(channel=channel)
        producer.register()

        producer.deregister()
        self.assertEqual(channel.producers, [])
        producer.deregister()
        self.assertEqual(channel.producers, [])

    async def test_publish(self):
        channel = MsgBroker(Scheduler.build()).add_channel('test_publish')
        consumer = Consumer(channel=channel)
        consumer.register()

        producer = Producer(channel=channel)
        msg = DataMsg(sender='test', headers=None, data=None)
        with self.assertRaises(RuntimeError):
            producer.publish(msg)

        producer.register()
        producer.publish(msg)
        consumer_msg = await consumer.get()
        self.assertEqual(consumer_msg, msg)

    async def test_invoke(self):
        channel = MsgBroker(Scheduler.build()).add_channel('test_invoke')
        consumer = Consumer(channel=channel)
        producer = Producer(channel=channel)
        consumer.register()
        producer.register()

        msg = producer.invoke(
            sender='test',
            headers={'corr_id': 123},
            cmd='cmd',
            cmd_args={'DEAD': 'CODE'}
        )
        self.assertIsInstance(msg, CmdMsg)
        self.assertEqual(msg.sender, 'test')
        self.assertEqual(msg.headers, {'corr_id': 123})
        self.assertEqual(msg.cmd, 'cmd')
        self.assertEqual(msg.cmd_args, {'DEAD': 'CODE'})

        consumed_msg = await consumer.get()
        self.assertEqual(msg, consumed_msg)

    async def test_feed(self):
        channel = MsgBroker(Scheduler.build()).add_channel('test_invoke')
        consumer = Consumer(channel=channel)
        producer = Producer(channel=channel)
        consumer.register()
        producer.register()

        msg = producer.feed(
            sender='test', headers={'corr_id': 123}, data='DEADCODE'
        )
        self.assertIsInstance(msg, DataMsg)
        self.assertEqual(msg.sender, 'test')
        self.assertEqual(msg.headers, {'corr_id': 123})
        self.assertEqual(msg.data, 'DEADCODE')

        consumed_msg = await consumer.get()
        self.assertEqual(msg, consumed_msg)

    async def test_notify(self):
        channel = MsgBroker(Scheduler.build()).add_channel('test_notify')
        consumer = Consumer(channel=channel)
        producer = Producer(channel=channel)
        consumer.register()
        producer.register()

        msg = producer.notify(
            sender='sender',
            headers={'corr_id': 1234},
            event='test_event',
            data=('DEAD', 'CODE')
        )
        self.assertIsInstance(msg, EventMsg)
        self.assertEqual(msg.sender, 'sender')
        self.assertEqual(msg.headers, {'corr_id': 1234})
        self.assertEqual(msg.event, 'test_event')
        self.assertEqual(msg.data, ('DEAD', 'CODE'))

        consumed_msg = await consumer.get()
        self.assertEqual(msg, consumed_msg)


class ConsumerTestCase(unittest.IsolatedAsyncioTestCase):
    def test__init__(self):
        channel = MsgBroker(Scheduler.build()).add_channel('test__init__')

        consumer = Consumer(channel=channel)
        self.assertEqual(consumer.channel, channel)
        self.assertEqual(consumer.registered, False)

    def test_register(self):
        channel = MsgBroker(Scheduler.build()).add_channel('test_register')
        consumer = Consumer(channel=channel)

        consumer.register()
        self.assertTrue(channel.consumers, [consumer])
        consumer.register()
        self.assertTrue(channel.consumers, [consumer])

    def test_deregister(self):
        channel = MsgBroker(Scheduler.build()).add_channel('test_deregister')
        consumer = Consumer(channel=channel)
        consumer.register()

        consumer.deregister()
        self.assertEqual(channel.consumers, [])
        consumer.deregister()
        self.assertEqual(channel.consumers, [])

    async def test_get(self):
        channel = MsgBroker(Scheduler.build()).add_channel('test_publish')
        producer = Producer(channel=channel)
        producer.register()
        msg = DataMsg(sender='test', headers=None, data=None)

        consumer = Consumer(channel=channel)
        with self.assertRaises(RuntimeError):
            await consumer.get()

        consumer.register()
        producer.publish(msg)
        consumer_msg = await consumer.get()
        self.assertEqual(consumer_msg, msg)


class MsgBrokerTestCase(unittest.IsolatedAsyncioTestCase):
    def test__init__(self):
        broker = MsgBroker(Scheduler.build())
        self.assertIsInstance(broker.wiretap_channel, Channel)
        self.assertIsInstance(broker.dead_letter_channel, Channel)
        self.assertIsInstance(broker.null_channel, Channel)

    async def test_build(self):
        broker = await MsgBroker.build(Scheduler.build())
        self.assertIsInstance(broker.wiretap_channel, Channel)
        self.assertIsInstance(broker.dead_letter_channel, Channel)
        self.assertIsInstance(broker.null_channel, Channel)
        self.assertTrue(broker.dispatcher_task in asyncio.all_tasks())

    def test_register_channel(self):
        broker = MsgBroker(Scheduler.build())
        channel = Channel(name='test_register_channel', broker=broker)

        broker.register_channel(channel)
        self.assertTrue('test_register_channel' in broker.channels)
        self.assertEqual(broker.channels['test_register_channel'], channel)

        with self.assertRaises(ValueError):
            broker.register_channel(channel)

    def test_deregister_channel(self):
        broker = MsgBroker(Scheduler.build())
        channel = Channel(name='test_deregister_channel', broker=broker)
        broker.register_channel(channel)

        broker.deregister_channel(channel)
        self.assertFalse('test_register_channel' in broker.channels)
        broker.deregister_channel(channel)

    def test_is_registered(self):
        broker = MsgBroker(Scheduler.build())
        channel1 = Channel(name='test_is_registered', broker=broker)
        channel2 = Channel(name='test_is_registered2', broker=broker)
        broker.register_channel(channel1)

        self.assertTrue(broker.is_registered(channel1))
        self.assertTrue(broker.is_registered(channel1.name))
        self.assertFalse(broker.is_registered(channel2))
        self.assertFalse(broker.is_registered(channel2.name))

    def test_add_channel(self):
        broker = MsgBroker(Scheduler.build())
        channel = broker.add_channel('test_add_channel')
        self.assertIsInstance(channel, Channel)
        self.assertTrue('test_add_channel' in broker.channels)
        self.assertTrue(broker.channels['test_add_channel'], channel)

    def test_get_channel(self):
        broker = MsgBroker(Scheduler.build())
        channel = broker.add_channel('test_get_channel')
        self.assertEqual(channel, broker.get_channel('test_get_channel'))
        with self.assertRaises(ValueError):
            broker.get_channel('test_get_channel2')

    def test_has_channel(self):
        broker = MsgBroker(Scheduler.build())
        broker.add_channel('test_has_channel')
        self.assertTrue(broker.has_channel('test_has_channel'))
        self.assertFalse(broker.has_channel('test_has_channel2'))

    def test_producer(self):
        broker = MsgBroker(Scheduler.build())
        channel = broker.add_channel('test_producer')

        producer = broker.producer(channel=channel)
        self.assertIsInstance(producer, Producer)
        self.assertEqual(producer.channel, channel)
        self.assertFalse(producer.registered)

        producer = broker.producer(channel='test_producer')
        self.assertEqual(producer.channel, channel)

        with self.assertRaises(ValueError):
            broker.producer(channel='test_producer2')

    def test_consumer(self):
        broker = MsgBroker(Scheduler.build())
        channel = broker.add_channel('test_consumer')

        consumer = broker.consumer(channel=channel)
        self.assertIsInstance(consumer, Consumer)
        self.assertEqual(consumer.channel, channel)
        self.assertFalse(consumer.registered)

        consumer = broker.consumer(channel='test_consumer')
        self.assertEqual(consumer.channel, channel)

        with self.assertRaises(ValueError):
            broker.consumer(channel='test_consumer2')

    async def test_publish(self):
        broker = await MsgBroker.build(Scheduler.build())
        channel1 = broker.add_channel('test_publish')
        channel2 = Channel('test_publish2', broker=broker)
        consumer = broker.consumer(channel='test_publish')
        consumer.register()

        # Publishing to a registered channel
        msg1 = DataMsg(sender='test', headers=None, data=None)
        broker.publish(channel=channel1, msg=msg1)
        self.assertIsInstance(msg1.timestamp, datetime.datetime)

        consumed_msg = await consumer.get()
        self.assertEqual(consumed_msg, msg1)

        msg2 = DataMsg(sender='test', headers=None, data=None)
        broker.publish(channel='test_publish', msg=msg2)
        self.assertIsInstance(msg2.timestamp, datetime.datetime)

        consumed_msg = await consumer.get()
        self.assertEqual(consumed_msg, msg2)

        # Publishing an unregistered channel
        msg1 = DataMsg(sender='test', headers=None, data=None)
        consumer = broker.consumer(channel=broker.dead_letter_channel)
        consumer.register()
        broker.publish(channel=channel2, msg=msg1)
        self.assertIsInstance(msg1.timestamp, datetime.datetime)

        consumed_msg = await consumer.get()
        self.assertIsInstance(consumed_msg, DeadLetterMsg)
        self.assertIsInstance(consumed_msg.timestamp, datetime.datetime)
        self.assertEqual(consumed_msg.msg, msg1)
        self.assertEqual(consumed_msg.channel_name, 'test_publish2')

        msg2 = DataMsg(sender='test', headers=None, data=None)
        broker.publish(channel='test_publish2', msg=msg2)
        self.assertIsInstance(msg2.timestamp, datetime.datetime)

        consumed_msg = await consumer.get()
        self.assertIsInstance(consumed_msg, DeadLetterMsg)
        self.assertIsInstance(consumed_msg.timestamp, datetime.datetime)
        self.assertEqual(consumed_msg.channel_name, 'test_publish2')
        self.assertEqual(consumed_msg.msg, msg2)
