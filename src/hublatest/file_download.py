import requests
import os
import sys

from tqdm import tqdm


class FileDownload:
    def __call__(self, url, file_path):
        self.url = url
        self.file_path = file_path
        self.download()

    def download(self):
        with open(self.file_path, "ab") as f:
            f.seek(0)
            f.truncate(0)
            total_size = None
            while f.tell() != total_size:
                headers = {}
                downloaded_bytes = f.tell()
                if total_size:
                    headers['Range'] = f'bytes={downloaded_bytes}-'
                response = requests.get(self.url, headers=headers, stream=True)
                
                if response.status_code == 206 and not downloaded_bytes or \
                        response.status_code == 200 and downloaded_bytes:
                    if response.status_code == 200:
                        raise Exception("Range header is not supported")
                    else:
                        raise Exception(
                            f"Server returned {response.status_code}")
                if total_size is None:
                    total_size = int(response.headers.get('content-length'))
                current_total_size = int(response.headers.get('content-length'))
                if current_total_size + downloaded_bytes != total_size:
                    raise Exception("Size changed")

                progress_bar = tqdm(
                    unit="B", unit_scale=True,
                    total=total_size,
                    disable=not os.isatty(sys.stderr.fileno()))
                progress_bar.update(downloaded_bytes)

                for chunk in response.iter_content(1024):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))


file_download = FileDownload()
