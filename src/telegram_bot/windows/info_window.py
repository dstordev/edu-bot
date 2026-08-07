from enum import Enum

import aiogram.exceptions
from aiogram import Bot
from aiogram.enums import InputMediaType, ParseMode
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InputMedia,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)
from loguru import logger


class MediaStrategy(Enum):
    """Стратегии работы с медиа в сообщении"""

    EDIT = "edit"  # Редактировать существующее
    DELETE_AND_SEND = "delete_and_send"  # Удалить и отправить новое
    SEND_NEW = "send_new"  # Отправить новое


class InfoWindow:
    """
    Улучшенная версия класса для работы с информационными окнами в Telegram боте.

    Основные улучшения:
    - Разделение ответственности на методы
    - Поддержка всех типов медиа
    - Настройка parse_mode
    - Лучшая обработка ошибок
    - Более читаемая логика
    """

    def __init__(
        self,
        text: str,
        inline_keyboard_markup: InlineKeyboardMarkup | None = None,
        media: InputMedia | None = None,
        parse_mode: ParseMode | None = ParseMode.HTML,
        disable_web_page_preview: bool = False,
        media_strategy: MediaStrategy = MediaStrategy.DELETE_AND_SEND,
    ):
        """
        Args:
            text: Текст сообщения (или caption для медиа)
            inline_keyboard_markup: Клавиатура
            media: Медиа-файл (фото, видео, документ и т.д.)
            parse_mode: Режим парсинга текста (HTML, Markdown)
            disable_web_page_preview: Отключить превью ссылок
            media_strategy: Стратегия работы с медиа при редактировании
        """
        self.text = text
        self.inline_keyboard_markup = inline_keyboard_markup
        self.media = media
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview
        self.media_strategy = media_strategy

    async def answer_window(self, event: CallbackQuery | Message) -> Message:
        """
        Основной метод для ответа на событие.

        Args:
            event: CallbackQuery или Message

        Returns:
            Message: Отправленное или отредактированное сообщение
        """
        if isinstance(event, CallbackQuery):
            return await self._handle_callback_query(event)
        elif isinstance(event, Message):
            return await self._handle_message(event)
        else:
            raise TypeError(f"Неподдерживаемый тип события: {type(event)}")

    async def _handle_callback_query(self, callback: CallbackQuery) -> Message:
        """Обработка CallbackQuery"""
        if not callback.message or not isinstance(callback.message, Message):
            raise ValueError("CallbackQuery не содержит сообщения")

        message = callback.message

        # Если нужно отправить/изменить медиа
        if self.media is not None:
            return await self._handle_media_in_callback(message)

        # Если в сообщении есть медиа, но мы хотим отправить текст
        if self._message_has_media(message):
            return await self._replace_media_with_text(message)

        # Простое редактирование текста
        if message.text is not None:
            return await self._edit_text(message)

        # Редактирование caption (если есть медиа без нашего media)
        if message.caption is not None:
            return await self._edit_caption(message)

        raise ValueError("Не удалось определить тип сообщения для редактирования")

    async def _handle_message(self, message: Message) -> Message:
        """Обработка обычного Message (отправка нового сообщения)"""
        if self.media is not None:
            return await self._send_media(message)

        return await message.answer(
            text=self.text,
            reply_markup=self.inline_keyboard_markup,
            parse_mode=self.parse_mode,
            disable_web_page_preview=self.disable_web_page_preview,
        )

    async def _handle_media_in_callback(self, message: Message) -> Message:
        """Обработка медиа в callback query"""
        # Если стратегия - редактировать и есть медиа в сообщении
        if self.media_strategy == MediaStrategy.EDIT and self._message_has_media(
            message
        ):
            try:
                # Обновляем медиа
                await message.edit_media(
                    media=self.media, reply_markup=self.inline_keyboard_markup
                )
                # Обновляем caption
                return await message.edit_caption(
                    caption=self.text,
                    reply_markup=self.inline_keyboard_markup,
                    parse_mode=self.parse_mode,
                )
            except aiogram.exceptions.TelegramBadRequest as e:
                logger.warning(
                    f"Не удалось отредактировать медиа: {e}. Попытка удалить и отправить заново..."
                )
                # Fallback на удаление и отправку

        # Удаляем старое сообщение и отправляем новое
        await self._safe_delete_message(message)
        return await self._send_media(message)

    async def _replace_media_with_text(self, message: Message) -> Message:
        """Заменить медиа-сообщение на текстовое"""
        if self.media_strategy == MediaStrategy.DELETE_AND_SEND:
            await self._safe_delete_message(message)
            return await message.answer(
                text=self.text,
                reply_markup=self.inline_keyboard_markup,
                parse_mode=self.parse_mode,
                disable_web_page_preview=self.disable_web_page_preview,
            )
        else:
            # Если стратегия EDIT, но нельзя отредактировать - отправляем новое
            return await message.answer(
                text=self.text,
                reply_markup=self.inline_keyboard_markup,
                parse_mode=self.parse_mode,
                disable_web_page_preview=self.disable_web_page_preview,
            )

    async def _edit_text(self, message: Message) -> Message:
        """Редактировать текст сообщения"""
        try:
            return await message.edit_text(
                text=self.text,
                reply_markup=self.inline_keyboard_markup,
                parse_mode=self.parse_mode,
                disable_web_page_preview=self.disable_web_page_preview,
            )
        except aiogram.exceptions.TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                logger.debug("Сообщение не изменилось, пропускаем редактирование")
                return message
            raise

    async def _edit_caption(self, message: Message) -> Message:
        """Редактировать caption медиа-сообщения"""
        try:
            return await message.edit_caption(
                caption=self.text,
                reply_markup=self.inline_keyboard_markup,
                parse_mode=self.parse_mode,
            )
        except aiogram.exceptions.TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                logger.debug("Caption не изменился, пропускаем редактирование")
                return message
            raise

    async def _send_media(self, message: Message) -> Message:
        """Отправить медиа-сообщение"""
        if self.media is None:
            raise ValueError("Media не установлено")

        media_type = self.media.type
        media_file = self.media.media

        send_kwargs = {
            "caption": self.text,
            "reply_markup": self.inline_keyboard_markup,
            "parse_mode": self.parse_mode,
        }

        # Определяем метод отправки в зависимости от типа медиа
        media_handlers = {
            InputMediaType.PHOTO: message.answer_photo,
            InputMediaType.VIDEO: message.answer_video,
            InputMediaType.AUDIO: message.answer_audio,
            InputMediaType.DOCUMENT: message.answer_document,
            InputMediaType.ANIMATION: message.answer_animation,
        }

        handler = media_handlers.get(media_type)
        if handler is None:
            raise ValueError(f"Неподдерживаемый тип медиа: {media_type}")

        # Для photo, video, animation, audio нужно передать первый аргумент как media
        return await handler(media_file, **send_kwargs)

    async def _safe_delete_message(self, message: Message) -> bool:
        """
        Безопасно удалить сообщение.

        Returns:
            bool: True если удалено, False если не удалось
        """
        try:
            await message.delete()
            return True
        except aiogram.exceptions.TelegramBadRequest as e:
            error_msg = str(e)
            if "message can't be deleted" in error_msg.lower():
                logger.warning(
                    f"Не удалось удалить сообщение {message.message_id}: "
                    "недостаточно прав или сообщение слишком старое"
                )
            elif "message to delete not found" in error_msg.lower():
                logger.warning(f"Сообщение {message.message_id} уже удалено")
            else:
                logger.error(f"Ошибка при удалении сообщения: {e}")
                raise
            return False

    @staticmethod
    def _message_has_media(message: Message) -> bool:
        """Проверить, содержит ли сообщение медиа"""
        return any(
            [
                message.photo,
                message.video,
                message.audio,
                message.document,
                message.animation,
                message.voice,
                message.video_note,
            ]
        )

    async def send_window(
        self,
        bot: Bot,
        chat_id: int,
        message_thread_id: int | None = None,
    ) -> Message:
        """
        Отправить окно напрямую через бота.

        Args:
            bot: Экземпляр бота
            chat_id: ID чата
            message_thread_id: ID топика (для супергрупп с топиками)

        Returns:
            Message: Отправленное сообщение
        """
        if self.media is not None:
            return await self._send_media_via_bot(bot, chat_id, message_thread_id)

        return await bot.send_message(
            chat_id=chat_id,
            text=self.text,
            reply_markup=self.inline_keyboard_markup,
            parse_mode=self.parse_mode,
            disable_web_page_preview=self.disable_web_page_preview,
            message_thread_id=message_thread_id,
        )

    async def _send_media_via_bot(
        self,
        bot: Bot,
        chat_id: int,
        message_thread_id: int | None = None,
    ) -> Message:
        """Отправить медиа через бота"""
        if self.media is None:
            raise ValueError("Media не установлено")

        media_type = self.media.type
        media_file = self.media.media

        send_kwargs = {
            "chat_id": chat_id,
            "caption": self.text,
            "reply_markup": self.inline_keyboard_markup,
            "parse_mode": self.parse_mode,
            "message_thread_id": message_thread_id,
        }

        # Определяем метод отправки
        media_handlers = {
            InputMediaType.PHOTO: bot.send_photo,
            InputMediaType.VIDEO: bot.send_video,
            InputMediaType.AUDIO: bot.send_audio,
            InputMediaType.DOCUMENT: bot.send_document,
            InputMediaType.ANIMATION: bot.send_animation,
        }

        handler = media_handlers.get(media_type)
        if handler is None:
            raise ValueError(f"Неподдерживаемый тип медиа: {media_type}")

        return await handler(media_file, **send_kwargs)

    # Convenience методы для создания окон

    @classmethod
    def text_window(
        cls,
        text: str,
        keyboard: InlineKeyboardMarkup | None = None,
        parse_mode: ParseMode | None = ParseMode.HTML,
    ) -> "InfoWindow":
        """Создать текстовое окно"""
        return cls(
            text=text,
            inline_keyboard_markup=keyboard,
            parse_mode=parse_mode,
        )

    @classmethod
    def photo_window(
        cls,
        photo: str | InputMediaPhoto,
        caption: str = "",
        keyboard: InlineKeyboardMarkup | None = None,
        parse_mode: ParseMode | None = ParseMode.HTML,
    ) -> "InfoWindow":
        """Создать окно с фото"""
        if isinstance(photo, str):
            photo = InputMediaPhoto(media=photo)
        return cls(
            text=caption,
            media=photo,
            inline_keyboard_markup=keyboard,
            parse_mode=parse_mode,
        )

    @classmethod
    def document_window(
        cls,
        document: str | InputMediaDocument,
        caption: str = "",
        keyboard: InlineKeyboardMarkup | None = None,
        parse_mode: ParseMode | None = ParseMode.HTML,
    ) -> "InfoWindow":
        """Создать окно с документом"""
        if isinstance(document, str):
            document = InputMediaDocument(media=document)
        return cls(
            text=caption,
            media=document,
            inline_keyboard_markup=keyboard,
            parse_mode=parse_mode,
        )

    def __repr__(self) -> str:
        """Строковое представление для отладки"""
        return (
            f"InfoWindow(text={self.text[:30]}..., "
            f"has_media={self.media is not None}, "
            f"has_keyboard={self.inline_keyboard_markup is not None})"
        )


# ==================== Дополнительные полезные классы ====================


class InfoWindowBuilder:
    """Builder паттерн для создания InfoWindow"""

    def __init__(self):
        self._text: str = ""
        self._keyboard: InlineKeyboardMarkup | None = None
        self._media: InputMedia | None = None
        self._parse_mode: ParseMode | None = ParseMode.HTML
        self._disable_web_page_preview: bool = False
        self._media_strategy: MediaStrategy = MediaStrategy.DELETE_AND_SEND

    def with_text(self, text: str) -> "InfoWindowBuilder":
        """Установить текст"""
        self._text = text
        return self

    def with_keyboard(self, keyboard: InlineKeyboardMarkup) -> "InfoWindowBuilder":
        """Установить клавиатуру"""
        self._keyboard = keyboard
        return self

    def with_photo(self, photo: str | InputMediaPhoto) -> "InfoWindowBuilder":
        """Добавить фото"""
        if isinstance(photo, str):
            photo = InputMediaPhoto(media=photo)
        self._media = photo
        return self

    def with_document(self, document: str | InputMediaDocument) -> "InfoWindowBuilder":
        """Добавить документ"""
        if isinstance(document, str):
            document = InputMediaDocument(media=document)
        self._media = document
        return self

    def with_video(self, video: str | InputMediaVideo) -> "InfoWindowBuilder":
        """Добавить видео"""
        if isinstance(video, str):
            video = InputMediaVideo(media=video)
        self._media = video
        return self

    def with_parse_mode(self, parse_mode: ParseMode) -> "InfoWindowBuilder":
        """Установить режим парсинга"""
        self._parse_mode = parse_mode
        return self

    def disable_preview(self) -> "InfoWindowBuilder":
        """Отключить превью ссылок"""
        self._disable_web_page_preview = True
        return self

    def with_media_strategy(self, strategy: MediaStrategy) -> "InfoWindowBuilder":
        """Установить стратегию работы с медиа"""
        self._media_strategy = strategy
        return self

    def build(self) -> InfoWindow:
        """Построить InfoWindow"""
        return InfoWindow(
            text=self._text,
            inline_keyboard_markup=self._keyboard,
            media=self._media,
            parse_mode=self._parse_mode,
            disable_web_page_preview=self._disable_web_page_preview,
            media_strategy=self._media_strategy,
        )
