"""Support for various asynchronous operations and extensions"""


import asyncio
import types
from typing import Any, Self


__all__ = ['Scheduler', 'AwaitableVar', 'Flag', 'Queue', 'Endpoint']


class Scheduler:
    """Class to manage scheduling (and running) asyncio tasks.

    Attributes:
        loop: The event loop.
        tasks: Set of running tasks.
    """

    loop: asyncio.AbstractEventLoop
    tasks: set[asyncio.Task]

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        """Initializes a Scheduler instance.

        Arguments:
            loop: The event loop to schedule with.
        """

        self.loop = loop
        self.tasks = set()

    @classmethod
    def build(cls, loop: asyncio.AbstractEventLoop = None) -> Self:
        """Builds new scheduler instances.

        Arguments:
            loop: The event loop for running tasks. Defaults to
                asyncio.get_event_loop().
        """

        if loop is None:
            loop = asyncio.get_event_loop()

        return cls(loop)

    def start_job(self, coro, *, name=None) -> asyncio.Task:
        """Schedules a job (coroutine) for running.

        Arguments:
            coro: The coroutine to schedule.
            name: Optional task name.

        Returns:
            An asyncio Task for the scheduled job.
        """

        task = self.loop.create_task(coro=coro, name=name)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

        return task


class AwaitableVar:
    """A variable that can be waited until a specific value is reached.

    Attributes:
        _value: The underlying value.
        value_change_events: Set of asyncio Events to notify when value is
            changed.
    """

    _value: Any
    value_change_events: set[asyncio.Event]

    def __init__(self, initial: Any = None) -> None:
        """Initializes an AwaitableVar instance.

        Arguments:
            initial: The initial value.
        """

        self._value = initial
        self.value_change_events = set()

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        self._value = new_value

        # Signal the value has changed
        for value_change_event in self.value_change_events:
            value_change_event.set()

    async def wait_for_value(self, value: Any) -> None:
        """Waits until a specific value is set.

        Notes:
            This does not spike the CPU. :)

        Arguments:
            value: The value to wait for.
        """

        if self.value == value:  # Do nothing if we're already there
            return

        # Set up to be notified
        value_changed_event = asyncio.Event()
        self.value_change_events.add(value_changed_event)

        # Block until we reach a specific value
        while self.value != value:
            await value_changed_event.wait()
            value_changed_event.clear()

        self.value_change_events.remove(value_changed_event)

    def __bool__(self) -> bool:
        return bool(self.value)


class Flag(AwaitableVar):
    """A flag that can be awaited until it is set (boolean AwaitableVar).

    This is similar to asyncio's Event, in that it can be used for signalling
    boolean events. However unlike the Event class, this class only returns
    for a specific waiter when the value is still set to the desired value.

    This last property helps avoid inconsistencies with Event. Essentially
    when you have multiple waiters on an Event, if the event is set and then
    cleared, all of the waiters will return from wait().  This class only
    returns to the waiters while the event is set. Thus you might have some
    return (then the flag gets cleared) and others continue waiting.
    """

    def __init__(self, initial: bool = False) -> None:
        """Initializes a Flag instance.

        Arguments:
            initial: The initial value.
        """

        super().__init__(initial)

    def set(self) -> None:
        """Sets the flag (to True)."""

        self.value = True

    def clear(self) -> None:
        """Clears the flag (sets to False)."""

        self.value = False

    def is_set(self) -> bool:
        """True if the flag is set."""

        return bool(self.value) is True

    def is_clear(self) -> bool:
        """True if the flag is cleared."""

        return bool(self.value) is not True

    async def wait(self) -> None:
        """Waits until the flag is set (to True)."""

        await self.wait_for_value(True)

    async def wait_clear(self) -> None:
        """Waits until the flag is cleared (set to False)."""

        await self.wait_for_value(False)


class Queue(asyncio.Queue):
    """Asynchronous queue that can be used for type hint contained items."""

    __class_getitem__ = classmethod(types.GenericAlias)


class Endpoint(asyncio.Protocol):
    """Network endpoint that provides a few socket-like functions.

    Attributes:
        connected: Set (True) when the socket is connected. Cleared (False)
            when not connected.
        writing_paused: True when transport's buffer goes over the high water
            mark, False when equal to or less than the high water mark.
        flush_awaiters: List of asyncio Futures awaiting on the flush() method.
        buffer: Buffer of bytes received
        buffer_awaiter: Future used for awaiting with the buffer_wait() method.
        transport: Underlying asynctio Transport instance.
        loop: The currently running event loop
    """

    connected: Flag
    writing_paused: bool
    flush_awaiters: list[asyncio.Future]
    buffer: bytearray
    buffer_awaiter: asyncio.Future | None
    transport: asyncio.Transport | None
    loop: asyncio.AbstractEventLoop

    def __init__(self) -> None:
        self.connected = Flag(False)
        self.writing_paused = True
        self.flush_awaiters = list()
        self.buffer = bytearray()
        self.buffer_awaiter = None
        self.transport = None
        self.loop = asyncio.get_event_loop()

    def connection_made(self, transport: asyncio.Transport) -> None:
        self.transport = transport
        self.connected.set()
        self.writing_paused = False

    def connection_lost(self, exc: Exception | None) -> None:
        self.connected.clear()
        self.writing_paused = True

    def data_received(self, data: bytes) -> None:
        self.buffer.extend(data)

        buffer_awaiter = self.buffer_awaiter
        if buffer_awaiter is not None:  # Wake up the buffer awaiter
            self.buffer_awaiter = None
            if not buffer_awaiter.cancelled():
                buffer_awaiter.set_result(None)

    def pause_writing(self) -> None:
        self.writing_paused = True

    # noinspection SpellCheckingInspection
    def resume_writing(self) -> None:
        self.writing_paused = False

        # Wake up any flush awaiters
        for awaiter in self.flush_awaiters:
            if not awaiter.done():
                awaiter.set_result(None)

    def getpeername(self) -> tuple[str, int]:
        """Gets the remote peer.

        Returns:
            A tuple of (host, port) for the remote system.
        """

        if not self.connected:
            return tuple()

        return self.transport.get_extra_info('peername')

    async def connect(self, host: str, port: int, **kwargs) -> None:
        """Opens a connection to a remote system.

        Arguments:
            host: The host to connect to.
            port: The port on the host to connect to.

        Notes;
            Additional keyword args are passed to the event loop's
            create_connection() method.
        """

        await self.loop.create_connection(lambda: self, host, port, **kwargs)

    async def close(self) -> None:
        """Closes the endpoint."""

        self.writing_paused = True
        self.connected.clear()
        self.transport.close()
        await asyncio.sleep(0)  # Give the transport a chance to actually close

    async def send(self, data: bytes) -> None:
        """Sends data over the network.

        Arguments:
            data: The data to send.
        """

        self.transport.write(data)
        await self.flush()

    async def flush(self) -> None:
        """Waits for the output buffer to be flushed (become available)."""

        if not self.writing_paused:
            return

        awaiter = self.loop.create_future()
        self.flush_awaiters.append(awaiter)

        try:
            await awaiter
        finally:
            self.flush_awaiters.remove(awaiter)

    async def recv(self, size: int) -> bytes:
        """Receives at most size bytes.

        Arguments:
            size: The maximum number of bytes to receive.

        Returns:
            At most size bytes.

        Raises:
            ValueError: If size is < 0.
        """

        if size < 0:
            raise ValueError(f'Invalid size {size}, must be >= 0')

        if size == 0:
            return b''

        if not self.buffer:  # Wait for the buffer to have some data
            await self.wait_for_buffer('recv')

        data = bytes(self.buffer[:size])
        del self.buffer[:size]

        return data

    async def recv_exactly(self, size: int) -> bytes:
        """Receives exactly size bytes.

        Arguments:
            size: The number of bytes to receive.

        Returns:
            The requested amount of bytes.

        Raises:
            ValueError: If size is less than 0.
        """

        if size < 0:
            raise ValueError(f'Invalid size {size}, must be >= 0')

        if size == 0:
            return b''

        while len(self.buffer) < size:
            await self.wait_for_buffer('recv_exactly')

        if len(self.buffer) == size:
            data = bytes(self.buffer)
            self.buffer.clear()
        else:
            data = bytes(self.buffer[:size])
            del self.buffer[:size]

        return data

    async def wait_for_buffer(self, caller_name: str) -> None:
        """Used to wait until the buffer has data.

        Arguments:
            caller_name: The function awaiting this method.
        """

        if self.buffer_awaiter is not None:
            raise RuntimeError(
                f'{caller_name}() called when another coroutine is awaiting '
                f'the buffer'
            )

        self.buffer_awaiter = self.loop.create_future()

        try:
            await self.buffer_awaiter
        finally:
            self.buffer_awaiter = None
