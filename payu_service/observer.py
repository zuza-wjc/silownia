from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
import threading

class Subject():
    def __init__(self):
        self._observers: List[Observer] = []
        self._lock = threading.Lock()


    def attach(self, observer: Observer) -> None:
        with self._lock:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        with self._lock:
            self._observers.remove(observer)

    def notify(self, data) -> None:
        with self._lock:
            observers_snapshot = list(self._observers)

        for observer in observers_snapshot:
            observer.update(self, data)

class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject, data) -> None:
        pass