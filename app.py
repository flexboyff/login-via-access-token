from flask import Flask, request, Response, render_template, jsonify
import requests
import json

app = Flask(__name__)
app.template_folder = "templates"

# In-memory storage
app.config["TOKEN_DATA"] = {}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("login_token.html")

    try:
        data = request.get_json()
        access_token = data.get("access_token")

        if not access_token:
            return jsonify({"error": "Access token required"}), 400

        api_url = f"https://ffmconnect.live.gop.garenanow.com/oauth/token/inspect?token={access_token}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }

        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code != 200:
            return jsonify({"error": "Token validation failed"}), 400

        inspect_data = response.json()

        token_data = {
            "code": 0,
            "data": {
                "uid": inspect_data.get("uid"),
                "open_id": inspect_data.get("open_id"),
                "expiry_time": inspect_data.get("expiry_time"),
                "refresh_expiry_time": inspect_data.get("expiry_time", 0) + 2592000 if inspect_data.get("expiry_time") else None,
                "platform": inspect_data.get("platform"),
                "main_active_platform": inspect_data.get("main_active_platform"),
                "create_time": inspect_data.get("create_time"),
                "scope": inspect_data.get("scope"),
                "access_token": access_token,
                "expires_in": 1296000,
                "token_type": "Bearer",
                "refresh_token": "e95a846287f18c652c1f0edf38bed6bb860233b5cd4424a660ba5dcce6cd65e7"
            }
        }

        app.config["TOKEN_DATA"] = token_data

        return jsonify({
            "success": True,
            "data": token_data["data"]
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/oauth/token/inspect", methods=["GET"])
def proxy_token_inspect():
    try:
        access_token = request.args.get("token")

        if not access_token:
            return jsonify({"error": "token parameter required"}), 400

        api_url = f"https://ffmconnect.live.gop.garenanow.com/oauth/token/inspect?token={access_token}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }

        response = requests.get(api_url, headers=headers, timeout=10)

        return Response(
            response.text,
            status=response.status_code,
            content_type="application/json"
        )

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/live/ver.php", methods=["GET"])
def live_version():
    try:
        base_url = "https://version.common.redflamenco.com/live/ver.php"
        query_string = request.query_string.decode()

        if query_string:
            api_url = f"{base_url}?{query_string}"
        else:
            api_url = base_url

        headers = {
            "User-Agent": request.headers.get("User-Agent", "Mozilla/5.0"),
            "Accept": "*/*"
        }

        response = requests.get(api_url, headers=headers, timeout=15)

        try:
            json_data = response.json()
            gop_url = json_data.get("gop_url")

            if gop_url:
                print("Original GOP URL:", gop_url)

                parts = gop_url.split(";")

                updated_parts = []
                for url in parts:
                    if "ffmconnect.live.gop.garenanow.com" in url:
                        updated_parts.append("https://version-common-redflamenco.vercel.app")
                    else:
                        updated_parts.append(url)

                json_data["gop_url"] = ";".join(updated_parts)

                return jsonify(json_data)

        except Exception:
            pass

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "text/plain")
        )

    except requests.exceptions.RequestException as e:
        return Response(str(e), status=500, content_type="text/plain")
    except Exception as e:
        return Response(str(e), status=500, content_type="text/plain")


@app.route("/api/v2/oauth/guest/token:grant", methods=["POST"])
def open_id():
    token_data = app.config.get("TOKEN_DATA")

    if not token_data:
        return jsonify({"error": "No token data available"}), 404

    return jsonify(token_data)


@app.route("/oauth/logout", methods=["GET"])
def oauth_logout():
    return jsonify({"result": 0})


@app.route("/api/token/info", methods=["GET"])
def get_token_info():
    token_data = app.config.get("TOKEN_DATA")

    if not token_data:
        return jsonify({"error": "No token info available"}), 404

    return jsonify(token_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
