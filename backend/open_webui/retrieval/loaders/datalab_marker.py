import json
import logging
import os
import time
from typing import List, Optional

import requests
from fastapi import HTTPException, status
from langchain_core.documents import Document

log = logging.getLogger(__name__)


class DatalabMarkerLoader:
    def __init__(
        self,
        file_path: str,
        api_key: str,
        api_base_url: str,
        additional_config: Optional[str] = None,
        use_llm: bool = False,
        skip_cache: bool = False,
        force_ocr: bool = False,
        paginate: bool = False,
        strip_existing_ocr: bool = False,
        disable_image_extraction: bool = False,
        format_lines: bool = False,
        output_format: str = "markdown",
    ):
        self.file_path = file_path
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.additional_config = additional_config
        self.use_llm = use_llm
        self.skip_cache = skip_cache
        self.force_ocr = force_ocr
        self.paginate = paginate
        self.strip_existing_ocr = strip_existing_ocr
        self.disable_image_extraction = disable_image_extraction
        self.format_lines = format_lines
        self.output_format = output_format

    def _get_mime_type(self, filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower()
        mime_map = {
            "pdf": "application/pdf",
            "xls": "application/vnd.ms-excel",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "ods": "application/vnd.oasis.opendocument.spreadsheet",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "odt": "application/vnd.oasis.opendocument.text",
            "ppt": "application/vnd.ms-powerpoint",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "odp": "application/vnd.oasis.opendocument.presentation",
            "html": "text/html",
            "epub": "application/epub+zip",
            "png": "image/png",
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "webp": "image/webp",
            "gif": "image/gif",
            "tiff": "image/tiff",
        }
        return mime_map.get(ext, "application/octet-stream")

    def load(self) -> List[Document]:
        filename = os.path.basename(self.file_path)
        mime_type = self._get_mime_type(filename)
        headers = {"X-Api-Key": self.api_key}

        form_data = {
            "use_llm": str(self.use_llm).lower(),
            "skip_cache": str(self.skip_cache).lower(),
            "force_ocr": str(self.force_ocr).lower(),
            "paginate": str(self.paginate).lower(),
            "strip_existing_ocr": str(self.strip_existing_ocr).lower(),
            "disable_image_extraction": str(self.disable_image_extraction).lower(),
            "format_lines": str(self.format_lines).lower(),
            "output_format": self.output_format,
        }

        if self.additional_config and self.additional_config.strip():
            form_data["additional_config"] = self.additional_config

        try:
            with open(self.file_path, "rb") as file_handle:
                files = {"file": (filename, file_handle, mime_type)}
                response = requests.post(
                    self.api_base_url,
                    data=form_data,
                    files=files,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()
        except FileNotFoundError:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail=f"File not found: {self.file_path}"
            )
        except requests.HTTPError as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Datalab Marker request failed: {exc}",
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                detail=f"Invalid JSON response: {exc}",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
            ) from exc

        if not result.get("success"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Datalab Marker request failed: {result.get("error", "Unknown error")}',
            )

        check_url = result.get("request_check_url")
        request_id = result.get("request_id")

        if check_url:
            for _ in range(300):
                time.sleep(2)
                try:
                    poll_response = requests.get(check_url, headers=headers)
                    poll_response.raise_for_status()
                    poll_result = poll_response.json()
                except (requests.HTTPError, ValueError) as exc:
                    raise HTTPException(
                        status.HTTP_502_BAD_GATEWAY,
                        detail=f"Polling failed: {exc}",
                    ) from exc

                status_val = poll_result.get("status")
                success_val = poll_result.get("success")
                if status_val == "complete":
                    break
                if status_val == "failed" or success_val is False:
                    error_msg = poll_result.get("error") or "Marker processing failed"
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        detail=f"Marker processing failed: {error_msg}",
                    )
            else:
                raise HTTPException(
                    status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Marker processing timed out",
                )

            raw_content = poll_result.get(self.output_format.lower())
            final_result = poll_result
        else:
            if "output" not in result:
                raise HTTPException(
                    status.HTTP_502_BAD_GATEWAY,
                    detail="Marker endpoint returned success but no output field",
                )
            raw_content = result.get("output")
            final_result = result

        if self.output_format.lower() == "json":
            full_text = json.dumps(raw_content, indent=2)
        elif self.output_format.lower() in {"markdown", "html"}:
            full_text = str(raw_content).strip()
        else:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported output format: {self.output_format}",
            )

        if not full_text:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Marker returned empty content",
            )

        metadata = {
            "source": filename,
            "output_format": final_result.get("output_format", self.output_format),
            "page_count": final_result.get("page_count", 0),
            "processed_with_llm": self.use_llm,
            "request_id": request_id or "",
        }

        images = final_result.get("images", {})
        if images:
            metadata["image_count"] = len(images)
            metadata["images"] = json.dumps(list(images.keys()))

        for key, value in metadata.items():
            if isinstance(value, (dict, list)):
                metadata[key] = json.dumps(value)
            elif value is None:
                metadata[key] = ""

        return [Document(page_content=full_text, metadata=metadata)]
