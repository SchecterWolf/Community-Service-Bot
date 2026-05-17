#!/usr/bin/env python3

import socket
import time
import boto3

from botocore.exceptions import ClientError
from enum import Enum

from config.Config import Config

class EC2State(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    SHUTTING_DOWN = "shutting-down"
    TERMINATED = "terminated"
    UNKNOWN = "unknown"


class MinecraftStat:
    def __init__(self, guildID: int):
        cfg = Config()
        self.instance_id = cfg.getConfig(guildID, "MCInstance")
        self.region_name = cfg.getConfig(guildID, "MCRegion")
        self.minecraft_host = cfg.getConfig(guildID, "MCHost")
        self.minecraft_port = 25565

        self.ec2 = boto3.client("ec2", region_name=self.region_name)

    def start(self) -> EC2State:
        """
        Request EC2 instance startup.
        """
        try:
            response = self.ec2.start_instances(
                InstanceIds=[self.instance_id]
            )
        except ClientError as exc:
            raise RuntimeError(f"Failed to start EC2 instance: {exc}") from exc

        state = response["StartingInstances"][0]["CurrentState"]["Name"]
        return EC2State(state)

    def get_status(self) -> EC2State:
        """
        Check current EC2 instance state.
        """
        try:
            response = self.ec2.describe_instances(
                InstanceIds=[self.instance_id]
            )
        except ClientError as exc:
            raise RuntimeError(f"Failed to describe EC2 instance: {exc}") from exc

        reservations = response.get("Reservations", [])
        if not reservations:
            return EC2State.UNKNOWN

        instances = reservations[0].get("Instances", [])
        if not instances:
            return EC2State.UNKNOWN

        state = instances[0]["State"]["Name"]
        return EC2State(state)

    def has_started(self) -> bool:
        """
        True once the EC2 instance is running.
        """
        return self.get_status() == EC2State.RUNNING

    def is_minecraft_port_open(self, timeout_seconds: float = 3.0) -> bool:
        """
        True once the Minecraft server port is reachable.
        """
        try:
            with socket.create_connection(
                (self.minecraft_host, self.minecraft_port),
                timeout=timeout_seconds,
            ):
                return True
        except OSError:
            return False

    def wait_until_running(self, timeout_seconds: int = 300) -> bool:
        """
        Wait until EC2 reaches running state.
        """
        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            if self.has_started():
                return True
            time.sleep(5)

        return False

    def wait_until_minecraft_ready(self, timeout_seconds: int = 600) -> bool:
        """
        Wait until the Minecraft port is reachable.
        """
        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            if self.is_minecraft_port_open():
                return True
            time.sleep(5)

        return False
