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
        blocks = self.lyrics_blocks_from_text(self.song_raw_text_edit.toPlainText())
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

    def current_song_data_from_form(self):
        self.update_song_slides_from_raw()
        sections = []
        for row in range(self.song_section_list.count()):
            section = dict(self.song_section_list.item(row).data(Qt.UserRole) or {})
            section["name"] = f"Slide {row + 1}"
            sections.append(section)
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
        title = self.song_title_edit.text().strip() or "Música"
        section = slide.get("name", "Slide") if isinstance(slide, dict) else "Slide"
        text = slide.get("text", "") if isinstance(slide, dict) else ""
        footer_parts = []
        if self.song_artist_edit.text().strip():
            footer_parts.append(self.song_artist_edit.text().strip())
        if self.song_author_edit.text().strip():
            footer_parts.append(self.song_author_edit.text().strip())
        if self.song_key_edit.text().strip():
            footer_parts.append(f"Tom: {self.song_key_edit.text().strip()}")
        if self.song_bpm_edit.text().strip():
            footer_parts.append(f"BPM: {self.song_bpm_edit.text().strip()}")
        background = None
        if isinstance(slide, dict):
            background = slide.get("background")
        if not background and self.song_default_background_path:
            background = {
                "type": self.song_default_background_type,
                "path": self.song_default_background_path,
            }
        background_type = background.get("type", "none") if isinstance(background, dict) else "none"
        background_path = background.get("path", "") if isinstance(background, dict) else ""
        song_style = {}
        selected_song = self.selected_song_from_list()
        if isinstance(selected_song, dict):
            song_style = dict(selected_song.get("style") or {})
        options = dict(song_style)
        options.update(
            {
                "text_case": self.song_text_case if self.song_text_case != "normal" else song_style.get("text_case", "normal"),
                "background_type": background_type,
                "background_path": background_path,
            }
        )
        return {
            "type": "text",
            "kind": "letra",
            "title": f"{title} · {section}",
            "body": text,
            "footer": " | ".join(footer_parts),
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
        """Return a safe song dictionary used by the lyrics module."""
        if not isinstance(song, dict):
            return None
        title = str(song.get("title") or song.get("titulo") or song.get("name") or "").strip()
        if not title:
            return None
        raw_lyrics = str(song.get("lyrics") or song.get("letra") or "").strip()
        raw_sections = song.get("sections") or song.get("slides") or song.get("trechos") or []
        sections = []
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
                if text:
                    sections.append({"name": name or f"Slide {index}", "text": text, "background": background})
        elif isinstance(raw_sections, dict):
            for index, (name, text) in enumerate(raw_sections.items(), start=1):
                if str(text).strip():
                    sections.append({"name": str(name) or f"Slide {index}", "text": str(text).strip(), "background": None})
        if not sections and raw_lyrics:
            sections = [
                {"name": f"Slide {index}", "text": block, "background": None}
                for index, block in enumerate(self.lyrics_blocks_from_text(raw_lyrics), start=1)
            ]
        if not raw_lyrics and sections:
            raw_lyrics = "\n\n".join(section.get("text", "") for section in sections)
        return {
            "title": title,
            "artist": str(song.get("artist") or song.get("artista") or "").strip(),
            "author": str(song.get("author") or song.get("autor") or "").strip(),
            "key": str(song.get("key") or song.get("tom") or "").strip(),
            "bpm": str(song.get("bpm") or "").strip(),
            "notes": str(song.get("notes") or song.get("anotacao") or song.get("anotação") or "").strip(),
            "copyright": str(song.get("copyright") or "").strip(),
            "lyrics": raw_lyrics,
            "default_background": song.get("default_background"),
            "sections": sections,
        }

    def parse_song_txt(self, text, default_title="Música importada"):
        """Parse a plain-text song.

        Metadata lines may appear at the top. After that, blank lines split slides.
        Bracket labels like [Refrão] are accepted and removed from the slide text.
        """
        metadata = {
            "title": "",
            "artist": "",
            "author": "",
            "key": "",
            "bpm": "",
            "notes": "",
            "copyright": "",
        }
        metadata_patterns = {
            "title": r"^(título|titulo|title|música|musica|song)\s*:\s*(.+)$",
            "artist": r"^(artista|artist|cantor|banda)\s*:\s*(.+)$",
            "author": r"^(autor|author|composer|compositor)\s*:\s*(.+)$",
            "key": r"^(tom|key)\s*:\s*(.+)$",
            "bpm": r"^(bpm|tempo)\s*:\s*(.+)$",
            "notes": r"^(anotação|anotacao|notes?)\s*:\s*(.+)$",
            "copyright": r"^(copyright|direitos)\s*:\s*(.+)$",
        }
        body_lines = []
        reading_body = False
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            matched_metadata = False
            if not reading_body:
                for key, pattern in metadata_patterns.items():
                    match = re.match(pattern, line, flags=re.IGNORECASE)
                    if match:
                        metadata[key] = match.group(2).strip()
                        matched_metadata = True
                        break
            if matched_metadata:
                continue
            if line.strip():
                reading_body = True
            if reading_body:
                body_lines.append(line)
        raw_lyrics = "\n".join(body_lines).strip()
        cleaned_blocks = []
        for block in self.lyrics_blocks_from_text(raw_lyrics):
            lines = block.splitlines()
            if lines and re.match(r"^\s*\[(.+?)\]\s*$", lines[0]):
                lines = lines[1:]
            cleaned = "\n".join(lines).strip()
            if cleaned:
                cleaned_blocks.append(cleaned)
        if not metadata["title"]:
            metadata["title"] = os.path.splitext(os.path.basename(default_title))[0]
        song = {
            **metadata,
            "lyrics": "\n\n".join(cleaned_blocks),
            "sections": [
                {"name": f"Slide {index}", "text": block, "background": None}
                for index, block in enumerate(cleaned_blocks, start=1)
            ],
        }
        return self.normalize_song_data(song)

    def song_to_txt(self, song):
        lines = [
            f"Título: {song.get('title', '')}",
            f"Artista: {song.get('artist', '')}",
            f"Autor: {song.get('author', '')}",
            f"Tom: {song.get('key', '')}",
            f"BPM: {song.get('bpm', '')}",
            f"Anotação: {song.get('notes', '')}",
            f"Copyright: {song.get('copyright', '')}",
            "",
        ]
        lyrics = song.get("lyrics") or "\n\n".join(
            section.get("text", "") for section in song.get("sections", []) if section.get("text")
        )
        lines.append(lyrics.strip())
        return "\n".join(lines).strip() + "\n"

    def upsert_imported_songs(self, songs):
        imported = 0
        for song in songs:
            normalized = self.normalize_song_data(song)
            if not normalized:
                continue
            self.songs = [s for s in self.songs if s.get("title") != normalized.get("title")]
            self.songs.append(normalized)
            imported += 1
        if imported:
            self.save_local_libraries()
            self.refresh_song_list()
            self.show_status_message(f"{imported} música(s) importada(s).", 5000)
        return imported

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
