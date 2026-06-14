import asyncio
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import settings
from app.engines.base import DownloadEngine, EngineProgress
from app.utils.encoding import decode_bytes, subprocess_env, title_from_task_file


class YtDlpEngine(DownloadEngine):
    name = "ytdlp"
    _processes: Dict[int, asyncio.subprocess.Process] = {}
    _progress: Dict[int, EngineProgress] = {}

    async def is_available(self) -> bool:
        path = settings.engines.ytdlp_path
        if shutil.which(path):
            return True
        return Path(path).exists()

    def _build_cmd(
        self, url: str, output_dir: str, task_id: int, options: dict[str, Any]
    ) -> list[str]:
        out_template = str(Path(output_dir) / f"task_{task_id}_%(title)s.%(ext)s")
        cmd = [
            settings.engines.ytdlp_path,
            "--newline",
            "--no-progress",
            "--progress-template",
            "download:%(progress.downloaded_bytes)s|%(progress.total_bytes)s|%(progress.speed)s|%(progress.eta)s",
            "-o",
            out_template,
        ]
        if options.get("audio_only"):
            cmd.extend(["-f", "bestaudio", "--extract-audio", "--audio-format", "mp3"])
        elif options.get("format"):
            cmd.extend(["-f", options["format"]])
        if options.get("subtitle"):
            cmd.extend(["--write-subs", "--write-auto-subs"])
        if options.get("cookies_file"):
            cmd.extend(["--cookies", options["cookies_file"]])
        cmd.append(url)
        return cmd

    async def start(
        self,
        task_id: int,
        url: str,
        output_dir: str,
        options: dict[str, Any],
    ) -> str:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        cmd = self._build_cmd(url, output_dir, task_id, options)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=subprocess_env(),
        )
        self._processes[task_id] = proc
        self._progress[task_id] = EngineProgress(status="running")
        asyncio.create_task(self._read_output(task_id, proc, output_dir))
        return str(task_id)

    async def _read_output(
        self, task_id: int, proc: asyncio.subprocess.Process, output_dir: str
    ) -> None:
        prog = self._progress.get(task_id, EngineProgress())
        output_lines: list[str] = []
        if proc.stdout:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = decode_bytes(line).strip()
                output_lines.append(text)
                if text.startswith("download:"):
                    self._parse_progress_line(task_id, text)
                if "[download] Destination:" in text:
                    path_part = text.split("Destination:", 1)[1].strip()
                    prog.file_path = path_part
                if "[Merger] Merging formats into" in text:
                    path_part = text.split("into", 1)[1].strip().strip('"')
                    prog.file_path = path_part
                if text.startswith("[download]") and "has already been downloaded" in text:
                    match = re.search(r"\[download\]\s+(.+?)\s+has already", text)
                    if match:
                        prog.file_path = match.group(1).strip()

        await proc.wait()
        prog = self._progress.get(task_id, EngineProgress())
        if proc.returncode == 0:
            prog.status = "completed"
            prog.progress = 100.0
            latest = self._find_latest_file(output_dir, task_id)
            if latest:
                prog.file_path = latest
            elif prog.file_path and not Path(prog.file_path).exists():
                prog.file_path = ""
            if prog.file_path:
                p = Path(prog.file_path)
                if p.exists():
                    prog.file_size = p.stat().st_size
                    prog.title = title_from_task_file(prog.file_path, task_id)
        else:
            prog.status = "failed"
            tail = "\n".join(output_lines[-5:])
            prog.error_message = tail or f"yt-dlp exited with code {proc.returncode}"
        self._progress[task_id] = prog
        self._processes.pop(task_id, None)

    def _parse_progress_line(self, task_id: int, line: str) -> None:
        parts = line.replace("download:", "").split("|")
        if len(parts) < 3:
            return
        prog = self._progress.get(task_id, EngineProgress())
        try:
            downloaded = int(parts[0]) if parts[0] else 0
            total = int(parts[1]) if parts[1] and parts[1] != "None" else 0
            speed_raw = parts[2]
            if total > 0:
                prog.progress = min(100.0, downloaded / total * 100.0)
            prog.speed = speed_raw if speed_raw and speed_raw != "None" else ""
        except (ValueError, TypeError):
            pass
        self._progress[task_id] = prog

    def _find_latest_file(self, output_dir: str, task_id: int) -> str:
        base = Path(output_dir)
        candidates = list(base.glob(f"task_{task_id}_*"))
        if not candidates:
            return ""
        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        return str(latest)

    async def poll(self, engine_task_id: str, task_id: int) -> EngineProgress:
        return self._progress.get(task_id, EngineProgress(status="running"))

    async def pause(self, engine_task_id: str, task_id: int) -> bool:
        proc = self._processes.get(task_id)
        if proc and proc.returncode is None:
            proc.terminate()
            prog = self._progress.get(task_id, EngineProgress())
            prog.status = "paused"
            self._progress[task_id] = prog
            return True
        return False

    async def cancel(self, engine_task_id: str, task_id: int) -> bool:
        proc = self._processes.get(task_id)
        if proc and proc.returncode is None:
            proc.kill()
        prog = self._progress.get(task_id, EngineProgress())
        prog.status = "cancelled"
        self._progress[task_id] = prog
        self._processes.pop(task_id, None)
        return True
