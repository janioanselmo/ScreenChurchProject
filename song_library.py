import json
import os
import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QListWidgetItem,
    QMessageBox,
    QDialog,
)

from song_dialogs import OnlineSongSearchDialog, SongEditorDialog


class SongLibraryMixin:
    """Song import, export, editing and projection helpers."""

    def selected_song_from_list(self):
        item = self.song_list.currentItem() if hasattr(self, "song_list") else None
        if item:
            return item.data(Qt.UserRole) or {}
        title = self.song_title_edit.text().strip() if hasattr(self, "song_title_edit") else ""
        if title:
            for song in self.songs:
                if song.get("title") == title:
                    return song
        return {}

    def open_online_song_search(self):
        dialog = OnlineSongSearchDialog(self)
        dialog.exec_()

    def open_new_song_editor(self):
        dialog = SongEditorDialog(self, {})
        if dialog.exec_() == QDialog.Accepted:
            self.save_song_data(dialog.song_data())

    def open_current_song_editor(self):
        song = self.selected_song_from_list()
        if not song:
            QMessageBox.information(self, "Música", "Selecione uma música para editar.")
            return
        dialog = SongEditorDialog(self, song)
        if dialog.exec_() == QDialog.Accepted:
            self.save_song_data(dialog.song_data(), previous_title=song.get("title"))

    def save_song_data(self, song, previous_title=None):
        song = self.normalize_song_data(song)
        if not song or not song.get("title"):
            QMessageBox.warning(self, "Música", "A música não possui título válido.")
            return
        remove_titles = {song.get("title")}
        if previous_title:
            remove_titles.add(previous_title)
        self.songs = [s for s in self.songs if s.get("title") not in remove_titles]
        self.songs.append(song)
        self.songs.sort(key=lambda item: item.get("title", "").lower())
        self.save_local_libraries()
        self.refresh_song_list()
        # Select and load the saved song.
        for row in range(self.song_list.count()):
            item = self.song_list.item(row)
            data = item.data(Qt.UserRole) or {}
            if data.get("title") == song.get("title"):
                self.song_list.setCurrentRow(row)
                self.load_song_to_form(item)
                break
        self.show_status_message(f"Música salva: {song['title']}", 4000)

    def new_song(self):
        self._updating_song_form = True
        self.song_title_edit.clear()
        self.song_artist_edit.clear()
        self.song_author_edit.clear()
        self.song_key_edit.clear()
        self.song_bpm_edit.clear()
        self.song_notes_edit.clear()
        self.song_copyright_edit.clear()
        self.song_default_background_type = "none"
        self.song_default_background_path = ""
        self.refresh_song_background_label()
        self.song_raw_text_edit.clear()
        self.song_section_list.clear()
        if hasattr(self, "song_current_label"):
            self.song_current_label.setText("Nenhuma música selecionada")
        self._updating_song_form = False
        self.song_title_edit.setFocus()

    def lyrics_blocks_from_text(self, text):
        """Split plain lyrics into slides using one or more blank lines."""
        text = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            return []
        blocks = re.split(r"\n\s*\n+", text)
        return [block.strip() for block in blocks if block.strip()]

    def song_title_author_text(self, song):
        """Return the mandatory first slide text for a song."""
        title = str(song.get("title", "")).strip()
        author = str(song.get("author") or song.get("artist") or "").strip()
        if title and author:
            return f"{title}\n{author}"
        return title

    def is_song_title_slide(self, song, section):
        """Check if a section is the mandatory title/author opening slide."""
        if not isinstance(section, dict):
            return False
        name = str(section.get("name", "")).strip().lower()
        text = str(section.get("text", "")).strip().lower()
        expected = self.song_title_author_text(song).strip().lower()
        return bool(expected and (name == "abertura" or text == expected))

    def current_slide_backgrounds(self):
        backgrounds = []
        for row in range(self.song_section_list.count()):
            data = self.song_section_list.item(row).data(Qt.UserRole) or {}
            backgrounds.append(data.get("background"))
        return backgrounds

    def update_song_slides_from_raw(self):
        if getattr(self, "_updating_song_form", False):
            return
        backgrounds = self.current_slide_backgrounds()
        current_row = max(self.song_section_list.currentRow(), 0)
        title_data = self.current_song_data_for_title()
        opening_text = self.song_title_author_text(title_data)
        lyric_blocks = [
            block for block in self.lyrics_blocks_from_text(self.song_raw_text_edit.toPlainText())
            if block.strip().lower() != opening_text.strip().lower()
        ]
        blocks = []
        if opening_text:
            blocks.append(opening_text)
        blocks.extend(lyric_blocks)
        self.song_section_list.clear()
        for index, block in enumerate(blocks, start=1):
            background = backgrounds[index - 1] if index - 1 < len(backgrounds) else None
            self.add_song_slide_item(index, block, background)
        if self.song_section_list.count():
            self.song_section_list.setCurrentRow(min(current_row, self.song_section_list.count() - 1))

    def add_song_slide_item(self, index, text, background=None):
        preview = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        preview = preview[:130] + ("..." if len(preview) > 130 else "")
        bg_marker = ""
        if isinstance(background, dict) and background.get("path"):
            bg_marker = "\n🖼/🎞 fundo próprio"
        item = QListWidgetItem(f"Slide {index}\n\n{preview}{bg_marker}")
        item.setToolTip(text)
        item.setData(
            Qt.UserRole,
            {
                "name": f"Slide {index}",
                "text": text,
                "background": background if isinstance(background, dict) else None,
            },
        )
        self.song_section_list.addItem(item)
        return item

    def refresh_song_background_label(self):
        if not hasattr(self, "song_default_background_label"):
            return
        if self.song_default_background_path:
            prefix = "Imagem" if self.song_default_background_type == "image" else "Vídeo"
            self.song_default_background_label.setText(
                f"Fundo padrão: {prefix} · {os.path.basename(self.song_default_background_path)}"
            )
        else:
            self.song_default_background_label.setText("Fundo padrão: sem fundo")

    def choose_song_default_background(self, media_type):
        filename = self.choose_text_background_file(media_type)
        if not filename:
            return
        self.song_default_background_type = media_type
        self.song_default_background_path = filename
        self.refresh_song_background_label()

    def clear_song_default_background(self):
        self.song_default_background_type = "none"
        self.song_default_background_path = ""
        self.refresh_song_background_label()

    def choose_song_slide_background(self, media_type):
        item = self.song_section_list.currentItem()
        if not item:
            QMessageBox.information(self, "Slide", "Selecione um slide antes de escolher o fundo.")
            return
        filename = self.choose_text_background_file(media_type)
        if not filename:
            return
        data = item.data(Qt.UserRole) or {}
        data["background"] = {"type": media_type, "path": filename}
        item.setData(Qt.UserRole, data)
        row = self.song_section_list.row(item)
        self.refresh_song_slide_item(row)

    def clear_song_slide_background(self):
        item = self.song_section_list.currentItem()
        if not item:
            return
        data = item.data(Qt.UserRole) or {}
        data["background"] = None
        item.setData(Qt.UserRole, data)
        self.refresh_song_slide_item(self.song_section_list.row(item))

    def choose_text_background_file(self, media_type):
        if media_type == "image":
            filter_text = "Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
            title = "Selecionar imagem de fundo"
        else:
            filter_text = "Vídeos (*.mp4 *.mov *.mkv *.avi *.wmv *.flv)"
            title = "Selecionar vídeo de fundo"
        filename, _ = QFileDialog.getOpenFileName(self, title, "", filter_text)
        return filename

    def refresh_song_slide_item(self, row):
        if row < 0 or row >= self.song_section_list.count():
            return
        item = self.song_section_list.item(row)
        data = item.data(Qt.UserRole) or {}
        text = data.get("text", "")
        background = data.get("background")
        preview = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        preview = preview[:130] + ("..." if len(preview) > 130 else "")
        bg_marker = ""
        if isinstance(background, dict) and background.get("path"):
            bg_marker = "\n🖼/🎞 fundo próprio"
        item.setText(f"Slide {row + 1}\n\n{preview}{bg_marker}")
        item.setToolTip(text)

    def current_song_data_for_title(self):
        """Small helper with current title/author fields."""
        return {
            "title": self.song_title_edit.text().strip(),
            "artist": self.song_artist_edit.text().strip(),
            "author": self.song_author_edit.text().strip(),
        }

    def current_song_data_from_form(self):
        self.update_song_slides_from_raw()
        lyric_sections = []
        for row in range(self.song_section_list.count()):
            section = dict(self.song_section_list.item(row).data(Qt.UserRole) or {})
            if self.is_song_title_slide(self.current_song_data_for_title(), section):
                continue
            section["name"] = f"Slide {row + 2}"
            lyric_sections.append(section)
        opening_text = self.song_title_author_text(self.current_song_data_for_title())
        sections = []
        if opening_text:
            sections.append({"name": "Abertura", "text": opening_text, "background": None})
        sections.extend(lyric_sections)
        default_background = None
        if self.song_default_background_path:
            default_background = {
                "type": self.song_default_background_type,
                "path": self.song_default_background_path,
            }
        return {
            "title": self.song_title_edit.text().strip(),
            "artist": self.song_artist_edit.text().strip(),
            "author": self.song_author_edit.text().strip(),
            "key": self.song_key_edit.text().strip(),
            "bpm": self.song_bpm_edit.text().strip(),
            "notes": self.song_notes_edit.text().strip(),
            "copyright": self.song_copyright_edit.text().strip(),
            "lyrics": self.song_raw_text_edit.toPlainText().strip(),
            "default_background": default_background,
            "sections": sections,
        }

    def save_current_song_section(self):
        """Compatibility method: raw lyrics are converted to slides automatically."""
        self.update_song_slides_from_raw()

    def save_song_from_form(self):
        self.save_song_data(self.current_song_data_from_form())

    def delete_current_song(self):
        song = self.selected_song_from_list()
        title = song.get("title") or self.song_title_edit.text().strip()
        if not title:
            return
        if QMessageBox.question(self, "Remover música", f"Remover '{title}'?") != QMessageBox.Yes:
            return
        self.songs = [s for s in self.songs if s.get("title") != title]
        self.save_local_libraries()
        self.refresh_song_list()
        self.new_song()

    def refresh_song_list(self):
        query = self.song_search.text().lower().strip() if hasattr(self, "song_search") else ""
        self.song_list.clear()
        for song in self.songs:
            searchable = " ".join(
                [
                    song.get("title", ""),
                    song.get("artist", ""),
                    song.get("author", ""),
                    song.get("lyrics", ""),
                    " ".join(s.get("text", "") for s in song.get("sections", [])),
                ]
            ).lower()
            if query and query not in searchable:
                continue
            subtitle = song.get("artist") or song.get("author") or ""
            item_text = song.get("title", "Sem título")
            if subtitle:
                item_text += f"\n{subtitle}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, song)
            self.song_list.addItem(item)

    def load_song_to_form(self, item):
        song = item.data(Qt.UserRole) or {}
        if hasattr(self, "song_current_label"):
            subtitle = song.get("artist") or song.get("author") or ""
            label = song.get("title", "Música")
            if subtitle:
                label += f"  ·  {subtitle}"
            self.song_current_label.setText(label)
        self._updating_song_form = True
        self.song_title_edit.setText(song.get("title", ""))
        self.song_artist_edit.setText(str(song.get("artist", "")))
        self.song_author_edit.setText(str(song.get("author", "")))
        self.song_key_edit.setText(str(song.get("key", "")))
        self.song_bpm_edit.setText(str(song.get("bpm", "")))
        self.song_notes_edit.setText(str(song.get("notes", "")))
        self.song_copyright_edit.setText(str(song.get("copyright", "")))
        background = song.get("default_background") or {}
        self.song_default_background_type = background.get("type", "none") if isinstance(background, dict) else "none"
        self.song_default_background_path = background.get("path", "") if isinstance(background, dict) else ""
        self.refresh_song_background_label()
        raw_text = song.get("lyrics") or "\n\n".join(
            section.get("text", "") for section in song.get("sections", []) if section.get("text", "")
        )
        self.song_raw_text_edit.setPlainText(raw_text)
        self.song_section_list.clear()
        sections = song.get("sections", [])
        if sections:
            for index, section in enumerate(sections, start=1):
                self.add_song_slide_item(index, section.get("text", ""), section.get("background"))
        else:
            for index, block in enumerate(self.lyrics_blocks_from_text(raw_text), start=1):
                self.add_song_slide_item(index, block)
        if self.song_section_list.count():
            self.song_section_list.setCurrentRow(0)
        self._updating_song_form = False

    def load_song_section_to_form(self, item):
        """Compatibility method kept for older signal connections."""
        return

    def selected_song_section_descriptor(self):
        self.update_song_slides_from_raw()
        item = self.song_section_list.currentItem()
        if not item and self.song_section_list.count():
            self.song_section_list.setCurrentRow(0)
            item = self.song_section_list.currentItem()
        slide = item.data(Qt.UserRole) if item else {}
        row = self.song_section_list.currentRow()
        if row < 0:
            row = 0
        title = self.song_title_edit.text().strip() or "Música"
        selected_song = self.selected_song_from_list()
        if not selected_song:
            selected_song = self.current_song_data_from_form()
        return self.build_song_section_descriptor(selected_song, row, slide=slide, title_override=title)

    def build_song_section_descriptor(self, song, section_index, slide=None, title_override=None, base_options=None):
        """Build a text descriptor for a song slide, including live keyboard navigation metadata."""
        song = song or {}
        sections = song.get("sections") or []
        if not sections:
            return {"type": "empty"}
        section_index = max(0, min(int(section_index or 0), len(sections) - 1))
        slide = slide if isinstance(slide, dict) else sections[section_index]
        title = title_override or song.get("title") or "Música"
        section = slide.get("name", f"Slide {section_index + 1}")
        text = slide.get("text", "")

        background = slide.get("background")
        if not background:
            background = song.get("default_background")
        background_type = background.get("type", "none") if isinstance(background, dict) else "none"
        background_path = background.get("path", "") if isinstance(background, dict) else ""

        song_style = dict(song.get("style") or {})
        options = dict(song_style)
        if isinstance(base_options, dict):
            options.update({k: v for k, v in base_options.items() if k != "_navigation"})
        options.update(
            {
                "text_case": self.song_text_case if self.song_text_case != "normal" else options.get("text_case", "normal"),
                "background_type": background_type,
                "background_path": background_path,
                "_navigation": {
                    "type": "song",
                    "title": song.get("title") or title,
                    "section_index": section_index,
                },
            }
        )
        return {
            "type": "text",
            "kind": "letra",
            "title": f"{title} · {section}",
            "body": text,
            "footer": "",
            "options": options,
        }

    def send_song_section_to_preview(self):
        descriptor = self.selected_song_section_descriptor()
        if descriptor["body"]:
            panel_index = self.song_target_panel_index()
            self.load_descriptor_to_preview(descriptor, panel_index)

    def send_song_section_to_live(self):
        descriptor = self.selected_song_section_descriptor()
        if descriptor["body"]:
            panel_index = self.song_target_panel_index()
            self.load_descriptor_to_preview(descriptor, panel_index)
            self.send_panel_to_live(panel_index)

    def add_song_section_to_service(self):
        descriptor = self.selected_song_section_descriptor()
        if descriptor["body"]:
            self.service_items.append({"label": descriptor["title"], "descriptor": descriptor})
            self.refresh_service_list()

    def normalize_song_data(self, song):
        """Return a safe song dictionary used by the lyrics module.

        Rule: every song always starts with an opening slide containing the
        full title and the author/artist on the second line. The remaining
        slides contain lyrics only.
        """
        if not isinstance(song, dict):
            return None
        title = str(song.get("title") or song.get("titulo") or song.get("name") or "").strip()
        if not title:
            return None

        normalized_base = {
            "title": title,
            "artist": str(song.get("artist") or song.get("artista") or "").strip(),
            "author": str(song.get("author") or song.get("autor") or "").strip(),
        }
        raw_lyrics = str(song.get("lyrics") or song.get("letra") or "").strip()
        raw_sections = song.get("sections") or song.get("slides") or song.get("trechos") or []
        lyric_sections = []

        if isinstance(raw_sections, list):
            for index, section in enumerate(raw_sections, start=1):
                background = None
                if isinstance(section, dict):
                    name = str(section.get("name") or section.get("title") or section.get("tipo") or f"Slide {index}").strip()
                    text = str(section.get("text") or section.get("body") or section.get("letra") or "").strip()
                    background = section.get("background")
                else:
                    name = f"Slide {index}"
                    text = str(section).strip()
                candidate = {"name": name, "text": text, "background": background}
                if text and not self.is_song_title_slide(normalized_base, candidate):
                    lyric_sections.append(candidate)
        elif isinstance(raw_sections, dict):
            for index, (name, text) in enumerate(raw_sections.items(), start=1):
                text = str(text).strip()
                candidate = {"name": str(name) or f"Slide {index}", "text": text, "background": None}
                if text and not self.is_song_title_slide(normalized_base, candidate):
                    lyric_sections.append(candidate)

        if raw_lyrics:
            lyric_sections = [
                {"name": f"Slide {index + 2}", "text": block, "background": None}
                for index, block in enumerate(self.lyrics_blocks_from_text(raw_lyrics))
                if block.strip().lower() != self.song_title_author_text(normalized_base).strip().lower()
            ] or lyric_sections
        elif lyric_sections:
            raw_lyrics = "\n\n".join(section.get("text", "") for section in lyric_sections)

        opening_text = self.song_title_author_text(normalized_base)
        sections = []
        if opening_text:
            sections.append({"name": "Abertura", "text": opening_text, "background": None})
        for index, section in enumerate(lyric_sections, start=2):
            sections.append(
                {
                    "name": f"Slide {index}",
                    "text": section.get("text", ""),
                    "background": section.get("background"),
                }
            )

        style = song.get("style") if isinstance(song.get("style"), dict) else {}
        normalized_style = {
            "text_case": str(style.get("text_case", "normal") or "normal"),
            "alignment": str(style.get("alignment", "center") or "center"),
            "font_size": int(style.get("font_size", 28) or 28),
            "text_color": str(style.get("text_color", "#ffffff") or "#ffffff"),
            "text_box_enabled": bool(style.get("text_box_enabled", True)),
            "text_box_color": str(style.get("text_box_color", "#000000") or "#000000"),
        }

        return {
            "title": title,
            "artist": normalized_base["artist"],
            "author": normalized_base["author"],
            "key": str(song.get("key") or song.get("tom") or "").strip(),
            "bpm": str(song.get("bpm") or "").strip(),
            "notes": str(song.get("notes") or song.get("anotacao") or song.get("anotação") or "").strip(),
            "copyright": str(song.get("copyright") or "").strip(),
            "lyrics": raw_lyrics,
            "default_background": song.get("default_background"),
            "style": normalized_style,
            "sections": sections,
        }

    def import_songs_json(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Importar músicas", "", "JSON (*.json)")
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
            songs = data.get("songs", data if isinstance(data, list) else [])
            imported = self.upsert_imported_songs(songs)
            if not imported:
                QMessageBox.information(self, "Importação", "Nenhuma música válida foi encontrada no JSON.")
        except (OSError, json.JSONDecodeError) as error:
            QMessageBox.warning(self, "Erro ao importar músicas", str(error))

    def export_songs_json(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Exportar músicas", "screenchurch_songs.json", "JSON (*.json)")
        if not filename:
            return
        if not filename.endswith(".json"):
            filename += ".json"
        with open(filename, "w", encoding="utf-8") as file:
            json.dump({"schema_version": 3, "songs": self.songs}, file, ensure_ascii=False, indent=2)
        self.show_status_message("Músicas exportadas em JSON.", 4000)

    def import_songs_txt(self):
        filenames, _ = QFileDialog.getOpenFileNames(self, "Importar músicas TXT", "", "Textos (*.txt)")
        if not filenames:
            return
        songs = []
        errors = []
        for filename in filenames:
            try:
                with open(filename, "r", encoding="utf-8") as file:
                    song = self.parse_song_txt(file.read(), filename)
                if song:
                    songs.append(song)
            except UnicodeDecodeError:
                try:
                    with open(filename, "r", encoding="latin-1") as file:
                        song = self.parse_song_txt(file.read(), filename)
                    if song:
                        songs.append(song)
                except OSError as error:
                    errors.append(f"{os.path.basename(filename)}: {error}")
            except OSError as error:
                errors.append(f"{os.path.basename(filename)}: {error}")
        imported = self.upsert_imported_songs(songs)
        if errors:
            QMessageBox.warning(self, "Importação parcial", "\n".join(errors))
        elif not imported:
            QMessageBox.information(self, "Importação", "Nenhuma música válida foi encontrada nos arquivos TXT.")

    def export_current_song_txt(self):
        song = self.current_song_data_from_form()
        if not song.get("title"):
            QMessageBox.information(self, "Exportar TXT", "Selecione ou preencha uma música antes de exportar.")
            return
        safe_title = re.sub(r"[^\w\-]+", "_", song.get("title", "musica"), flags=re.UNICODE).strip("_") or "musica"
        filename, _ = QFileDialog.getSaveFileName(self, "Exportar música TXT", f"{safe_title}.txt", "Textos (*.txt)")
        if not filename:
            return
        if not filename.endswith(".txt"):
            filename += ".txt"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(self.song_to_txt(song))
        self.show_status_message(f"Música exportada: {os.path.basename(filename)}", 4000)

    # ------------------------------------------------------------------
    # Bible plugin/importer
    # ------------------------------------------------------------------
