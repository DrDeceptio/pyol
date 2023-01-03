import asyncio
import unittest

from pyol.lib.aio import AwaitableVar, Endpoint, Flag, Scheduler


class MockJob:
    """Simple class used for testing async code."""

    def __init__(self):
        self.entered = False
        self.proceed = False
        self.exited = False

        self.connected = False
        self.running = False
        self.reader = None
        self.writer = None

    async def start_job_test(self):
        self.entered = True
        self.exited = True

    async def wait_for_value_test(self, avar, target_value):
        self.entered = True
        while not self.proceed:
            await avar.wait_for_value(target_value)
            await asyncio.sleep(0)
        self.exited = True

    async def sneaky_wait_for_value_test(self, avar, target_value):
        """Same as wait_for_value_test but resets the value before exiting."""

        self.entered = True
        orig_value = avar.value
        await avar.wait_for_value(target_value)
        avar.value = orig_value
        self.exited = True

    async def wait_test(self, flag):
        self.entered = True
        while not self.proceed:
            await flag.wait()
            await asyncio.sleep(0)
        self.exited = True

    async def sneaky_wait_test(self, flag):
        """Same as wait_test but resets the flag before exiting."""
        self.entered = True
        await flag.wait()
        flag.clear()
        self.exited = True

    async def connect_test_server(self):
        self.entered = True
        server = await asyncio.start_server(
            self.connect_test_handler, '127.0.0.1', 5190
        )

        try:
            self.running = True
            await server.serve_forever()
        finally:
            server.close()

        self.exited = True

    def connect_test_handler(self, reader, writer):
        """Helper for the server"""
        self.connected = True
        self.reader = reader
        self.writer = writer

    async def send_test(self, endpoint: Endpoint):
        self.entered = True
        await endpoint.send(b'\xDE\xAD\xC0\xDE')
        self.exited = True

    async def flush_test(self, endpoint):
        self.entered = True
        await endpoint.flush()
        self.exited = True

    async def recv_test(self, endpoint, size):
        self.entered = True
        result = await endpoint.recv(size)
        self.exited = True
        return result

    async def recv_exactly_test(self, endpoint, size):
        self.entered = True
        result = await endpoint.recv_exactly(size)
        self.exited = True
        return result

    async def wait_for_buffer_test(self, endpoint):
        self.entered = True
        await endpoint.wait_for_buffer('test')
        self.exited = True


class MockTransport(asyncio.Transport):
    """Mock transport for testing."""

    def __init__(self):
        super().__init__()
        self.buffer = bytearray()
        self.closed = False

    def write(self, data):
        self.buffer.extend(data)

    def get_extra_info(self, name, default=None):
        if name == 'peername':
            return '127.0.0.1', 5190
        else:
            return default

    def close(self):
        self.closed = True


class SchedulerTestCase(unittest.IsolatedAsyncioTestCase):
    def test__build__(self):
        scheduler = Scheduler.build()
        self.assertEqual(scheduler.loop, asyncio.get_event_loop())
        self.assertEqual(scheduler.tasks, set())

    async def test_start_job(self):
        mock_job = MockJob()
        scheduler = Scheduler.build()

        job = scheduler.start_job(mock_job.start_job_test())
        self.assertEqual(scheduler.tasks, {job})
        self.assertTrue(job in asyncio.all_tasks())
        self.assertFalse(mock_job.entered)
        self.assertFalse(job.done())
        self.assertFalse(mock_job.exited)

        await asyncio.sleep(0)

        self.assertTrue(mock_job.entered)
        self.assertTrue(job.done())
        self.assertTrue(mock_job.exited)


class AwaitableVarTestCase(unittest.IsolatedAsyncioTestCase):
    def test__init__(self):
        avar = AwaitableVar()
        self.assertEqual(avar._value, None)
        self.assertEqual(avar.value_change_events, set())

        avar = AwaitableVar('pyol')
        self.assertEqual(avar._value, 'pyol')

    def test__bool__(self):
        items = [
            (1, True),
            (0, False),
            (True, True),
            (False, False),
            ('false', True),
            ('', False)
        ]

        for test, expected in items:
            with self.subTest(test=test):
                avar = AwaitableVar(test)
                self.assertEqual(bool(avar), expected)

    def test_value(self):
        avar = AwaitableVar('pyol')
        self.assertEqual(avar.value, 'pyol')

        avar.value = 0xDEADC0DE
        self.assertEqual(avar.value, 0xDEADC0DE)

    async def test_wait_for_value(self):
        mj = MockJob()
        avar = AwaitableVar()

        task1 = asyncio.create_task(mj.wait_for_value_test(avar, 0xFF))
        self.assertFalse(mj.entered)
        self.assertFalse(mj.exited)
        self.assertFalse(task1.done())

        # Give it a chance to start
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertFalse(mj.exited)
        self.assertFalse(task1.done())
        mj.proceed = True

        # Set it to something other than the target
        avar.value = 'not what we want'
        await asyncio.sleep(0)
        self.assertFalse(mj.exited)
        self.assertFalse(task1.done())

        # Give it a chance to run with the target value
        avar.value = 0xFF
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertTrue(mj.exited)
        self.assertTrue(task1.done())

        # Now test interleaved waiting with a sneaky task.

        avar = AwaitableVar('pyol')
        mj1 = MockJob()
        mj2 = MockJob()

        # Start the normal wait_for_value_test
        task1 = asyncio.create_task(mj1.wait_for_value_test(avar, 0xFF))
        await asyncio.sleep(0)
        self.assertTrue(mj1.entered)
        self.assertFalse(mj1.exited)
        self.assertFalse(task1.done())

        # Start the sneaky waiter
        task2 = asyncio.create_task(mj2.sneaky_wait_for_value_test(avar, 0xFF))
        await asyncio.sleep(0)
        self.assertFalse(mj1.exited)
        self.assertFalse(task1.done())
        self.assertTrue(mj2.entered)
        self.assertFalse(mj2.exited)
        self.assertFalse(task2.done())

        # Make sure both tasks are still running
        await asyncio.sleep(0)
        self.assertFalse(mj1.exited)
        self.assertFalse(task1.done())
        self.assertFalse(mj2.exited)
        self.assertFalse(task2.done())

        # Let task2 proceed
        avar.value = 0xFF
        await asyncio.sleep(0)

        # Make sure task1 is running, task2 is done
        self.assertFalse(mj1.exited)
        self.assertFalse(task1.done())
        self.assertTrue(mj2.exited)
        self.assertTrue(task2.done())

        # Let task1 proceed
        mj1.proceed = True
        avar.value = 0xFF
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertTrue(mj1.exited)
        self.assertTrue(task1.done())


class FlagTestCase(unittest.IsolatedAsyncioTestCase):
    def test_set(self):
        flag = Flag(False)
        flag.set()
        self.assertTrue(flag.value)

    def test_clear(self):
        flag = Flag(True)
        flag.clear()
        self.assertFalse(flag.value)

    def test_is_set(self):
        flag = Flag()
        self.assertFalse(flag.is_set())
        flag.set()
        self.assertTrue(flag.is_set())

    def test_is_clear(self):
        flag = Flag()
        self.assertTrue(flag.is_clear())
        flag.set()
        self.assertFalse(flag.is_clear())

    async def test_wait(self):
        mj = MockJob()
        flag = Flag()

        task1 = asyncio.create_task(mj.wait_test(flag))
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertFalse(mj.exited)
        self.assertFalse(task1.done())

        # Set the flag and let it proceed
        flag.set()
        mj.proceed = True
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertTrue(mj.exited)
        self.assertTrue(task1.done())

        # Now with interleaved waiting using a sneaky task
        flag = Flag()
        mj1 = MockJob()
        mj2 = MockJob()

        # Start the normal wait_test method
        task1 = asyncio.create_task(mj1.wait_test(flag))
        await asyncio.sleep(0)
        self.assertTrue(mj1.entered)
        self.assertFalse(mj1.exited)
        self.assertFalse(task1.done())

        # Start the sneaky wait_test method
        task2 = asyncio.create_task(mj2.sneaky_wait_test(flag))
        await asyncio.sleep(0)

        # Make sure both are still running
        self.assertFalse(mj1.exited)
        self.assertFalse(task1.done())
        self.assertTrue(mj2.entered)
        self.assertFalse(mj2.exited)
        self.assertFalse(task2.done())

        # Set the flag and only let task2 run
        flag.set()
        await asyncio.sleep(0)

        # Make sure task1 is running, task2 is exited
        self.assertFalse(mj1.exited)
        self.assertFalse(task1.done())
        self.assertTrue(mj2.exited)
        self.assertTrue(task2.done())
        self.assertTrue(flag.is_clear())

        # Let task1 proceed
        mj1.proceed = True
        flag.set()
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertTrue(mj1.exited)
        self.assertTrue(task1.done())


class EndpointTestCase(unittest.IsolatedAsyncioTestCase):
    def test__init__(self):
        endpoint = Endpoint()

        self.assertFalse(endpoint.connected)
        self.assertTrue(endpoint.writing_paused)

    def test_connection_made(self):
        endpoint = Endpoint()
        mt = MockTransport()

        endpoint.connection_made(mt)
        self.assertTrue(endpoint.connected)

    def test_connection_lost(self):
        endpoint = Endpoint()
        mt = MockTransport()

        endpoint.connection_made(mt)
        endpoint.connection_lost(None)
        self.assertFalse(endpoint.connected)

    def test_data_received(self):
        endpoint = Endpoint()
        mt = MockTransport()
        endpoint.connection_made(mt)

        endpoint.data_received(b'\xDE\xAD')
        self.assertEqual(endpoint.buffer, b'\xDE\xAD')

        endpoint.data_received(b'\xC0\xDE')
        self.assertEqual(endpoint.buffer, b'\xDE\xAD\xC0\xDE')

        # Note: Testing the buffer_awaiter is done implicitly elsewhere

    def test_pause_writing(self):
        endpoint = Endpoint()
        mt = MockTransport()

        endpoint.connection_made(mt)
        endpoint.pause_writing()
        self.assertTrue(endpoint.writing_paused)

    def test_resume_writing(self):
        endpoint = Endpoint()
        mt = MockTransport()

        endpoint.connection_made(mt)
        endpoint.pause_writing()
        endpoint.resume_writing()
        self.assertFalse(endpoint.writing_paused)
        # Note: Testing the flush_awaits is done implicitly elsewhere

    def test_get_peername(self):
        endpoint = Endpoint()
        mt = MockTransport()

        endpoint.connection_made(mt)
        self.assertEqual(endpoint.getpeername(), ('127.0.0.1', 5190))

    async def test_connect(self):
        endpoint = Endpoint()
        sj = MockJob()

        # Start a local listener
        server_task = asyncio.create_task(sj.connect_test_server())
        async with asyncio.timeout(5):
            while not sj.running:
                await asyncio.sleep(0)
        self.assertTrue(sj.entered)
        self.assertFalse(sj.connected)
        self.assertFalse(sj.exited)
        self.assertFalse(server_task.done())

        # Connect the endpoint
        await endpoint.connect('127.0.0.1', 5190)
        self.assertTrue(endpoint.connected)
        self.assertFalse(endpoint.writing_paused)

        # Stop the listener
        server_task.cancel()
        await asyncio.sleep(0)

    async def test_close(self):
        endpoint = Endpoint()
        mt = MockTransport()

        endpoint.connection_made(mt)
        await endpoint.close()
        self.assertFalse(endpoint.connected)
        self.assertTrue(endpoint.writing_paused)
        self.assertTrue(mt.closed)

    async def test_send(self):
        endpoint = Endpoint()
        mt = MockTransport()
        mj = MockJob()

        endpoint.connection_made(mt)

        # Run the send task, writing is not paused
        send_task = asyncio.create_task(mj.send_test(endpoint))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertTrue(mj.exited)
        self.assertEqual(mt.buffer, b'\xDE\xAD\xC0\xDE')
        self.assertTrue(send_task.done())

        # Run the send task, with writing paused
        mj = MockJob()
        mt.buffer.clear()
        endpoint.pause_writing()
        send_task = asyncio.create_task(mj.send_test(endpoint))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertFalse(mj.exited)
        self.assertFalse(send_task.done())
        self.assertEqual(mt.buffer, b'\xDE\xAD\xC0\xDE')

        # Resume writing to allow the send to finish
        endpoint.resume_writing()
        await asyncio.sleep(0)
        self.assertTrue(mj.exited)
        self.assertTrue(send_task.done())

    async def test_flush(self):
        mt = MockTransport()
        mj = MockJob()
        endpoint = Endpoint()

        endpoint.connection_made(mt)
        endpoint.pause_writing()
        flush_task = asyncio.create_task(mj.flush_test(endpoint))
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertFalse(mj.exited)
        self.assertFalse(flush_task.done())

        endpoint.resume_writing()
        await asyncio.sleep(0)
        self.assertTrue(mj.exited)
        self.assertTrue(flush_task.done())

    async def test_recv(self):
        mt = MockTransport()
        endpoint = Endpoint()
        mj = MockJob()

        endpoint.connection_made(mt)
        endpoint.data_received(b'\xDE\xAD\xC0\xDE')

        # Test with 0 bytes requested
        recv_task = asyncio.create_task(mj.recv_test(endpoint, 0))
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertTrue(mj.exited)
        self.assertTrue(recv_task.done())
        self.assertEqual(recv_task.result(), b'')

        # Test with 4 bytes requested
        mj = MockJob()
        recv_task = asyncio.create_task(mj.recv_test(endpoint, 4))
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertTrue(mj.exited)
        self.assertTrue(recv_task.done())
        self.assertEqual(recv_task.result(), b'\xDE\xAD\xC0\xDE')
        self.assertEqual(endpoint.buffer, b'')

        # Test with reading less than the full buffer size
        endpoint.data_received(b'\xDE\xAD\xC0\xDE\xFF\xFF\xFF\xFF')
        mj = MockJob()
        recv_task = asyncio.create_task(mj.recv_test(endpoint, 4))
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertTrue(mj.exited)
        self.assertTrue(recv_task.done())
        self.assertEqual(recv_task.result(), b'\xDE\xAD\xC0\xDE')
        self.assertEqual(endpoint.buffer, b'\xFF\xFF\xFF\xFF')

        # Test with reading more than the buffer size
        endpoint.buffer.clear()
        endpoint.data_received(b'\x55\xAA')
        mj = MockJob()
        recv_task = asyncio.create_task(mj.recv_test(endpoint, 4))
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertTrue(mj.exited)
        self.assertTrue(recv_task.done())
        self.assertTrue(recv_task.result(), b'\x55\xAA')

        # Test with empty buffer (initially)
        endpoint.buffer.clear()
        mj = MockJob()
        recv_task = asyncio.create_task(mj.recv_test(endpoint, 4))
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertFalse(mj.exited)
        self.assertFalse(recv_task.done())

        # Feed some data
        endpoint.data_received(b'\xDE\xAD\xC0\xDE')
        await asyncio.sleep(0)
        self.assertTrue(mj.exited)
        self.assertTrue(recv_task.done())
        self.assertEqual(recv_task.result(), b'\xDE\xAD\xC0\xDE')

    async def test_recv_exactly(self):
        endpoint = Endpoint()
        mt = MockTransport()
        mj = MockJob()
        endpoint.connection_made(mt)

        #
        # Test with 0 bytes to receive
        #
        recv_task = asyncio.create_task(mj.recv_exactly_test(endpoint, 0))
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertTrue(mj.exited)
        self.assertTrue(recv_task.done())

        #
        # Test with less bytes than buffer, no waiting
        #
        mj = MockJob()
        endpoint.data_received(b'\xDE\xAD\xC0\xDE')
        recv_task = asyncio.create_task(mj.recv_exactly_test(endpoint, 2))
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertTrue(mj.exited)
        self.assertTrue(recv_task.done())
        self.assertEqual(recv_task.result(), b'\xDE\xAD')
        self.assertEqual(endpoint.buffer, b'\xC0\xDE')

        #
        # Test with exactly the right amount of bytes, no waiting
        #
        mj = MockJob()
        endpoint.buffer.clear()
        endpoint.data_received(b'\xDE\xAD\xC0\xDE')
        recv_task = asyncio.create_task(mj.recv_exactly_test(endpoint, 4))
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertTrue(mj.exited)
        self.assertTrue(recv_task.done())
        self.assertEqual(recv_task.result(), b'\xDE\xAD\xC0\xDE')
        self.assertEqual(endpoint.buffer, b'')

        #
        # Test with waiting, buffer initially empty, feed one byte at a time
        #
        mj = MockJob()
        endpoint.buffer.clear()
        recv_task = asyncio.create_task(mj.recv_exactly_test(endpoint, 4))
        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertFalse(mj.exited)
        self.assertFalse(recv_task.done())

        # Feed first byte
        endpoint.data_received(b'\xDE')
        await asyncio.sleep(0)
        self.assertFalse(mj.exited)
        self.assertFalse(recv_task.done())

        # Feed the second byte
        endpoint.data_received(b'\xAD')
        await asyncio.sleep(0)
        self.assertFalse(mj.exited)
        self.assertFalse(recv_task.done())

        # Feed the third byte
        endpoint.data_received(b'\xC0')
        await asyncio.sleep(0)
        self.assertFalse(mj.exited)
        self.assertFalse(recv_task.done())

        # Feed the fourth byte
        endpoint.data_received(b'\xDE')
        await asyncio.sleep(0)
        self.assertTrue(mj.exited)
        self.assertTrue(recv_task.done())
        self.assertEqual(recv_task.result(), b'\xDE\xAD\xC0\xDE')
        self.assertEqual(endpoint.buffer, b'')

    async def test_wait_for_buffer(self):
        mt = MockTransport()
        endpoint = Endpoint()
        mj = MockJob()

        endpoint.connection_made(mt)
        buffer_task = asyncio.create_task(mj.wait_for_buffer_test(endpoint))

        await asyncio.sleep(0)
        self.assertTrue(mj.entered)
        self.assertFalse(mj.exited)
        self.assertFalse(buffer_task.done())
        endpoint.data_received(b'\xDE\xAD\xC0\xDE')
        await asyncio.sleep(0)
        self.assertTrue(mj.exited)
        self.assertTrue(buffer_task.done())

        # Verify multiple awaiters raises an error
        endpoint.buffer.clear()
        mj1 = MockJob()
        mj2 = MockJob()
        task1 = asyncio.create_task(mj1.wait_for_buffer_test(endpoint))
        await asyncio.sleep(0)
        self.assertTrue(mj1.entered)
        self.assertFalse(mj1.exited)
        self.assertFalse(task1.done())
        with self.assertRaises(RuntimeError):
            await mj2.wait_for_buffer_test(endpoint)

        self.assertTrue(mj2.entered)
        self.assertFalse(mj2.exited)
        task1.cancel()
        await asyncio.sleep(0)
