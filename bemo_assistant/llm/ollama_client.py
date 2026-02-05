import json
import base64
import requests


class OllamaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def health(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self):
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=4)
            resp.raise_for_status()
            data = resp.json()
            return [m.get("name") for m in data.get("models", [])]
        except Exception:
            return []

    def chat_stream(self, messages, model: str, temperature: float = 0.6):
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature},
        }
        with requests.post(
            f"{self.base_url}/api/chat", json=payload, stream=True, timeout=60
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                data = json.loads(line.decode("utf-8"))
                if data.get("done"):
                    break
                message = data.get("message", {})
                yield message.get("content", "")

    def chat(self, messages, model: str, temperature: float = 0.6):
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")

    def chat_with_image(self, messages, model: str, temperature: float = 0.6):
        # Ollama accepts base64 images in the message "images" list
        prepared = []
        for msg in messages:
            new_msg = dict(msg)
            images = new_msg.get("images")
            if images:
                encoded = []
                for img_path in images:
                    with open(img_path, "rb") as f:
                        encoded.append(base64.b64encode(f.read()).decode("utf-8"))
                new_msg["images"] = encoded
            prepared.append(new_msg)

        payload = {
            "model": model,
            "messages": prepared,
            "stream": False,
            "options": {"temperature": temperature},
        }
        resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")
