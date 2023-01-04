"""Internal messaging"""


from __future__ import annotations
import abc
import asyncio
from datetime import datetime, timezone
from enum import Enum, auto
import itertools
from typing import Any, ClassVar, Iterator, Self, TypeVar

from pyol.lib.aio import Scheduler, Queue


__all__ = [
    'MsgIntent', 'CmdReply', 'Msg', 'MsgType', 'CmdMsg', 'DataMsg', 'EventMsg',
    'WiretapMsg', 'DeadLetterMsg', 'Channel', 'Producer', 'Consumer',
    'MsgBroker',
]


class MsgIntent(Enum):
    """Enumeration for differing message intents."""

    CMD = auto()
    DATA = auto()
    EVENT = auto()
    INVALID = auto()
    DEADLETTER = auto()
    WIRETAP = auto()


class CmdReply(Enum):
    """Enumeration for replies to command messages."""

    DONE = auto()
    UNKNOWN_CMD = auto()


class Msg(abc.ABC):
    """A message sent to an internal service/component/etc.

    Attributes:
        intent: The message intent.
        sender: The message sender.
        headers: Mapping of message headers.
        timestamp: The timestamp when the message was sent (not created).
        msg_id: Unique message identifier.
    """

    intent: MsgIntent
    sender: str
    headers: dict[str, Any]
    timestamp: datetime | None
    msg_id: int

    msg_id_counter: ClassVar[Iterator] = itertools.count()

    def __init__(
            self,
            intent: MsgIntent,
            sender: str,
            headers: dict[str, Any] | None,
    ) -> None:
        """Initializes a Msg instance.

        Arguments:
            intent: The message intent.
            sender: The message sender (usually a service).
            headers: Optional message headers.
        """

        self.intent = intent
        self.sender = sender
        self.msg_id = next(self.msg_id_counter)
        self.timestamp = None
        self.headers = dict()

        if headers is not None:
            self.add_headers(**headers)

    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'msg_id={self.msg_id}, '
            f'intent={self.intent}, '
            f'sender=\'{self.sender}\', '
            f'headers={self.headers}, '
            f')'
        )

    def __repr__(self) -> str:
        return self.__str__()

    def add_headers(self, **headers) -> None:
        """Adds multiple header fields.

        All headers must be specified as keyword arguments.
        """

        if not headers:
            return

        for name, value in headers.items():
            self.headers[name] = value


MsgType = TypeVar('MsgType', bound=Msg)


class CmdMsg(Msg):
    """A message for invoking a command or some functionality.

    Attributes:
        cmd: The command/functionality to invoke.
        cmd_args: Dictionary of argument name/value pairs to pass to cmd.
    """

    cmd: str
    cmd_args: dict[str, any]

    def __init__(
            self,
            sender: str,
            headers: dict[str, Any] | None,
            cmd: str,
            cmd_args: dict[str, Any] | None = None
    ) -> None:
        """Initializes a CmdMsg instance.

        Arguments:
            sender: The message sender.
            headers: Optional message headers.
            cmd: The command/functionality to invoke.
            cmd_args: Dictionary of command arguments.
        """

        super().__init__(intent=MsgIntent.CMD, sender=sender, headers=headers)

        if cmd_args is None:
            cmd_args = dict()

        self.cmd = cmd
        self.cmd_args = cmd_args

    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'msg_id={self.msg_id}, '
            f'intent={self.intent}, '
            f'sender=\'{self.sender}\', '
            f'headers={self.headers}, '
            f'cmd=\'{self.cmd}\', '
            f'cmd_args={self.cmd_args}, '
            f')'
        )

    def __repr__(self) -> str:
        return self.__str__()


class DataMsg(Msg):
    """A message containing arbitrary data.

    Attributes:
        data: The data.
    """

    data: Any

    def __init__(
            self,
            sender: str,
            headers: dict[str, Any] | None,
            data: Any
    ) -> None:
        """Initializes a DataMsg instance.

        Arguments:
            sender: The message sender.
            headers: Optional message ehaders.
            data: The data.
        """

        super().__init__(intent=MsgIntent.DATA, sender=sender, headers=headers)
        self.data = data

    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'msg_id={self.msg_id}, '
            f'intent={self.intent}, '
            f'sender=\'{self.sender}\', '
            f'headers={self.headers}, '
            f'data={self.data}, '
            f')'
        )

    def __repr__(self) -> str:
        return self.__str__()


class EventMsg(Msg):
    """Messages for events.

    Attributes:
        event: The event that occurred.
        data: Optional event data.
    """

    event: str
    data: Any

    def __init__(
            self,
            sender: str,
            headers: dict[str, Any] | None,
            event: str,
            data: Any = None
    ) -> None:
        """Initializes an EventMsg instance.

        Arguments:
            sender: The message sender.
            headers: Optional message headers.
            event: The event that occurred.
            data: Optional event data.
        """

        super().__init__(
            intent=MsgIntent.EVENT, sender=sender, headers=headers
        )
        self.event = event
        self.data = data

    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'msg_id={self.msg_id}, '
            f'intent={self.intent}, '
            f'sender=\'{self.sender}\', '
            f'headers={self.headers}, '
            f'event=\'{self.event}\', '
            f'data={self.data}, '
            f')'
        )

    def __repr__(self) -> str:
        return self.__str__()


class DeadLetterMsg(Msg):
    """For undeliverable messages.

    Attributes:
        channel_name: The channel name the message was originally published on.
        msg: The message that was published.
    """

    channel_name: str
    msg: MsgType

    def __init__(self, channel_name: str, msg: MsgType) -> None:
        """Initializes a WiretapMsg instance.

        Arguments:
            channel_name: The channel name msg was originally published on.
            msg: The message that was published.
        """

        super().__init__(
            intent=MsgIntent.DEADLETTER, sender='deadletter', headers=None
        )
        self.channel_name = channel_name
        self.msg = msg

    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'msg_id={self.msg_id}, '
            f'intent={self.intent}, '
            f'channel_name=\'{self.channel_name}\', '
            f'msg={self.msg}, '
            f')'
        )

    def __repr__(self) -> str:
        return self.__str__()


class WiretapMsg(Msg):
    """For wiretapped messages.

    Attributes:
        channel: The channel the message was originally published on.
        msg: The message that was published.
    """

    channel: Channel
    msg: MsgType

    def __init__(self, channel: Channel, msg: MsgType) -> None:
        """Initializes a WiretapMsg instance.

        Arguments:
            channel: The channel the message was originally published on.
            msg: The message that was published.
        """

        super().__init__(
            intent=MsgIntent.WIRETAP, sender='wiretap', headers=None
        )
        self.channel = channel
        self.msg = msg

    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'msg_id={self.msg_id}, '
            f'intent={self.intent}, '
            f'channel=\'{self.channel.name}\', '
            f'msg={self.msg}, '
            f')'
        )

    def __repr__(self) -> str:
        return self.__str__()


class Channel:
    """The medium for transmitting messages.

    Attributes:
        name: The channel identifier.
        broker: The MsgBroker instance that handles channel communication.
        producers: List of channel Producer instances.
        consumers: List of channel Consumer instances.
    """

    name: str
    broker: MsgBroker
    producers: list[Producer]
    consumers: list[Consumer]

    def __init__(self, name: str, broker: MsgBroker) -> None:
        """Initializes a Channel instance.

        Arguments:
            name: The channel identifier.
            broker: The MsgBroker instance that handles channel communication.
        """

        self.name = name
        self.broker = broker
        self.producers = list()
        self.consumers = list()

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(name=\'{self.name}\')'

    def __repr__(self) -> str:
        return self.__str__()

    def register_producer(self, producer: Producer) -> None:
        """Registers a producer with a Channel instance.

        Notes:
            This method is idempotent. That is, registering a producer that is
            already registered essentially does nothing.

        Arguments:
            producer: The producer to register.
        """

        if producer not in self.producers:
            self.producers.append(producer)

    def deregister_producer(self, producer: Producer) -> None:
        """Deregisters a producer from the Channel instance.

        Notes:
            This method is idempotent. That is, deregistering a producer that
            is no longer (or never was) registered essentially does nothing.

        Arguments:
            producer: The producer to deregister.
        """

        if producer in self.producers:
            self.producers.remove(producer)

    def register_consumer(self, consumer: Consumer) -> None:
        """Registers a consumer with a Channel instance.

        Notes:
            This method is idempotent. That is, registering a consumer that is
            already registered essentially does nothing. This is to avoid
            double-delivery of the same message.

        Arguments:
            consumer: The consumer to register.
        """

        if consumer not in self.consumers:
            self.consumers.append(consumer)

    def deregister_consumer(self, consumer: Consumer) -> None:
        """Deregisters a consumer from the Channel instance.

        Notes:
            This method is idempotent. That is, deregistering a consumer that
            is no longer (or never was) registered essentially does nothing.

        Arguments:
            consumer: The consumer to deregister.
        """

        if consumer in self.consumers:
            self.consumers.remove(consumer)


class Participant(abc.ABC):
    """Base class for participant (Producer and Consumer) classes.

    Attributes:
        channel: The Channel instance to participate with.
        registered: True if registered with the channel, False if not.
    """

    channel: Channel
    registered: bool

    def __init__(self, channel: Channel) -> None:
        """Initializes a Participant instance.

        Arguments:
            channel: The Channel instance to participate with.
        """

        self.channel = channel
        self.registered = False

    @abc.abstractmethod
    def register(self) -> None:
        """Registers the participant with their Channel instance."""

        raise NotImplementedError

    @abc.abstractmethod
    def deregister(self) -> None:
        """Deregisters the participant from their Channel instance."""

        raise NotImplementedError

    def __enter__(self) -> Self:
        self.register()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.deregister()


class Producer(Participant):
    """Class to publish messages on a Channel instance."""

    def register(self) -> None:
        self.channel.register_producer(self)
        self.registered = True

    def deregister(self) -> None:
        self.channel.deregister_producer(self)
        self.registered = False

    def publish(self, msg: MsgType) -> None:
        """Publishes a message on the producer's channel.

        Arguments:
            msg: The message to publish.

        Raises:
            RuntimeError: If not registered.
        """

        if not self.registered:
            raise RuntimeError(
                f'Producer is not registered with channel {self.channel.name}'
            )

        self.channel.broker.publish(self.channel, msg)

    def invoke(
            self,
            sender: str,
            headers: dict[str, Any] | None,
            cmd: str,
            cmd_args: dict[str, Any] | None = None
    ) -> CmdMsg:
        """Publishes a command message.

        Arguments:
            sender: The message sender.
            headers: Optional message headers.
            cmd: The command/functionality to invoke.
            cmd_args: Optional command arguments.

        Returns:
            The CmdMsg instance that was published.
        """

        msg = CmdMsg(
            sender=sender, headers=headers, cmd=cmd, cmd_args=cmd_args
        )
        self.publish(msg)
        return msg

    def feed(
            self,
            sender: str,
            headers: dict[str, Any] | None,
            data: Any
    ) -> DataMsg:
        """Publishes a data message.

        Arguments:
            sender: The message sender.
            headers: Optional message headers.
            data: The data.

        Returns:
            The DataMsg instance that was published.
        """

        msg = DataMsg(sender=sender, headers=headers, data=data)
        self.publish(msg)
        return msg

    def notify(
            self,
            sender: str,
            headers: dict[str, Any] | None,
            event: str,
            data: Any = None
    ) -> EventMsg:
        """Publishes an event message.

        Arguments:
            sender: The message sender.
            headers: Optional message headers.
            event: The event that occurred.
            data: Optional event data.

        Returns:
            The EventMsg instance that was published.
        """

        msg = EventMsg(sender=sender, headers=headers, event=event, data=data)
        self.publish(msg)
        return msg


class Consumer(Participant):
    """For consuming messages from a channel.

    Attributes:
        in_queue: Queue of incoming messages.
    """

    in_queue: Queue[MsgType]

    def __init__(self, channel: Channel) -> None:
        super().__init__(channel)
        self.in_queue = Queue()

    def register(self) -> None:
        self.channel.register_consumer(self)
        self.registered = True

    def deregister(self) -> None:
        self.channel.deregister_consumer(self)
        self.registered = False

    def msg_received(self, msg: MsgType) -> None:
        self.in_queue.put_nowait(msg)

    async def get(self) -> MsgType:
        """Gets a single message.

        Returns:
            The message that was received.

        Raises:
            RuntimeError: If not registered on the channel.
        """

        if not self.registered:
            raise RuntimeError(
                f'Consumer is not registered with {self.channel.name}'
            )

        msg = await self.in_queue.get()
        return msg


class MsgBroker:
    """Broker to handle messaging.

    Attributes:
        in_queue: Queue of incoming channel/message tuples that are to be
            published to various consumers.
        channels: Dictionary of channel names -> instances.
        wiretap_channel: The channel for wiretapped messages.
        dead_letter_channel: The channel for undeliverable messages.
        null_channel: The messaging equivalent of /dev/null (i.e. no
            consumers).
        dispatcher_task: An asyncio Task for the dispatcher() method.
    """

    in_queue: Queue[tuple[Channel, MsgType]]
    channels: dict[str, Channel]
    wiretap_channel: Channel
    dead_letter_channel:  Channel
    null_channel: Channel
    dispatcher_task: asyncio.Task

    def __init__(self, scheduler: Scheduler) -> None:
        """Initializes a MsgBroker instance.

        Arguments:
            scheduler: A scheduler for running jobs.
        """

        self.in_queue = Queue()
        self.channels = dict()
        self.wiretap_channel = self.add_channel('wiretap')
        self.dead_letter_channel = self.add_channel('dead_letter')
        self.null_channel = self.add_channel('null')

        self.dispatcher_task = scheduler.start_job(self.dispatcher())

    @classmethod
    async def build(cls, scheduler: Scheduler) -> Self:
        """Builds a MsgBroker instance.

        Arguments:
            scheduler: A scheduler for running jobs.

        Returns:
            A newly created MsgBroker instance.
        """

        broker = cls(scheduler)
        await asyncio.sleep(0)  # Give the dispatcher a chance to start
        return broker

    def register_channel(self, channel: Channel) -> None:
        """Registers a Channel instance with the broker.

        Arguments:
            channel: The channel to register.

        Raises:
            ValueError: If the channel is already registered.
        """

        if channel.name in self.channels:
            raise ValueError(f'Channel {channel.name} already registered')

        self.channels[channel.name] = channel

    def deregister_channel(self, channel: Channel) -> None:
        """Deregisters a Channel instance from the broker.

        Arguments:
            channel: The channel to deregister.

        Notes:
            If channel is not registered, this method essentially does nothing.
        """

        if channel.name in self.channels:
            del self.channels[channel.name]

    def is_registered(self, channel: Channel | str) -> bool:
        """Determine if a channel is registered with the broker.

        Arguments:
            channel: A Channel instance or name.

        Returns:
            True if channel is registered, False if not.
        """

        if isinstance(channel, str):
            channel_name = channel
        else:
            channel_name = channel.name

        return channel_name in self.channels

    def add_channel(self, name: str) -> Channel:
        """Adds a channel to the broker.

        Arguments:
            name: The name of the channel.

        Returns:
            The Channel instance.

        Notes:
            This method is idempotent. Calling it multiple times with the same
            name returns the same Channel instance.
        """

        if name in self.channels:
            return self.channels[name]

        channel = Channel(name=name, broker=self)
        self.register_channel(channel)

        return channel

    def get_channel(self, name: str) -> Channel:
        """Gets a Channel instance by name.

        Arguments:
            name: The name of the channel.

        Returns:
            The Channel instance with that name.

        Raises:
            ValueError: If there is no Channel registered with name.
        """

        if name not in self.channels:
            raise ValueError(f'Unknown Channel \'{name}\'')

        return self.channels[name]

    def has_channel(self, name: str) -> bool:
        """Determines if a channel is registered (by name).

        Arguments:
            name: The name of the channel.

        Returns:
            True if the channel is registered, False if not.
        """

        return name in self.channels

    def producer(self, channel: Channel | str) -> Producer:
        """Creates a new Producer instance.

        Notes:
            This method does not register the producer.

        Arguments:
            channel: Either a Channel instance, or the name of one. The channel
                must already be registered with the broker.

        Returns:
            A Producer instance.

        Raises:
            ValueError: If channel is not registered with the broker.
        """

        if isinstance(channel, str):
            channel_name = channel
        else:
            channel_name = channel.name

        if channel_name not in self.channels:
            raise ValueError(f'Unknown channel \'{channel_name}\'')

        channel = self.channels[channel_name]
        producer = Producer(channel=channel)
        return producer

    def consumer(self, channel: Channel | str) -> Consumer:
        """Creates a new consumer instance.

        Notes:
            This method does *not* register the consumer.

        Arguments:
            channel: Either a Channel instance, or the name of one. The channel
                must already be registered with the broker.

        Returns:
            A Consumer instance.

        Raises:
            ValueError: If channel is not registered with the broker.
        """

        if isinstance(channel, str):
            channel_name = channel
        else:
            channel_name = channel.name

        if channel_name not in self.channels:
            raise ValueError(f'Unknown channel \'{channel_name}\'')

        channel = self.channels[channel_name]
        consumer = Consumer(channel=channel)
        return consumer

    async def dispatcher(self) -> None:
        """Handles dispatching published messages."""

        while True:
            channel, msg = await self.in_queue.get()
            for consumer in channel.consumers:
                consumer.msg_received(msg)

    def publish(self, channel: Channel | str, msg: Msg) -> None:
        """Publishes a message on a channel.

        Arguments:
            channel: The channel to publish on (name or Channel instance).
            msg: The message to publish.

        Notes:
            Publishing to non-existent/unregistered channels sends the message
            to the dead letter channel.
        """

        msg.timestamp = datetime.now(timezone.utc)

        if isinstance(channel, str):
            channel_name = channel
        else:
            channel_name = channel.name

        if channel_name not in self.channels:
            msg = DeadLetterMsg(channel_name=channel_name, msg=msg)
            msg.timestamp = datetime.now(timezone.utc)
            channel = self.dead_letter_channel
        else:
            channel = self.channels[channel_name]

        self.in_queue.put_nowait((channel, msg))
