#!/usr/bin/env python3
"""Social engagement tracker — polls all accessible platforms and generates a unified report."""
import json, os, urllib.request, datetime, pathlib

# Auto-load .env if present (for cron context where env vars aren't pre-exported)
_env = pathlib.Path(__file__).resolve().parent.parent / ".env"
if _env.exists():
    with open(_env) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

API_KEY = os.environ.get("MATON_API_KEY", "")
REPO = "/home/ubuntu/.openclaw/workspace"
LOG = os.path.join(REPO, "exports/social/engagement-log.json")
DASHBOARD = os.path.join(REPO, "exports/social/dashboard.json")

def load_log():
    if os.path.exists(LOG):
        with open(LOG) as f:
            return json.load(f)
    return {"platforms": {}, "history": []}

def save_log(data):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "w") as f:
        json.dump(data, f, indent=2)

def check_moltbook():
    """Check Moltbook activity"""
    mb_key = os.environ.get("MOLTBOOK_API_KEY", "")
    try:
        req = urllib.request.Request(
            "https://www.moltbook.com/api/v1/home",
            headers={"Authorization": f"Bearer {mb_key}"}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        acct = data.get("your_account", {})
        posts_data = data.get("posts_from_accounts_you_follow", {})
        activity = data.get("activity_on_your_posts", [])
        
        # Get my posts with engagement
        req2 = urllib.request.Request(
            "https://www.moltbook.com/api/v1/posts?author=trevormentis",
            headers={"Authorization": f"Bearer {mb_key}"}
        )
        resp2 = urllib.request.urlopen(req2, timeout=10)
        my_posts = json.loads(resp2.read()).get("posts", [])
        
        total_upvotes = sum(p.get("upvotes", 0) for p in my_posts)
        total_comments = sum(p.get("comment_count", 0) for p in my_posts)
        
        return {
            "karma": acct.get("karma", 0),
            "followers": acct.get("follower_count", 0),
            "notifications": acct.get("unread_notification_count", 0),
            "post_count": len(my_posts),
            "total_upvotes": total_upvotes,
            "total_comments": total_comments,
            "posts": [{
                "id": p["id"],
                "title": p["title"][:60],
                "submolt": p.get("submolt", {}).get("name", "?"),
                "upvotes": p.get("upvotes", 0),
                "comments": p.get("comment_count", 0),
                "spam": p.get("is_spam", False)
            } for p in my_posts]
        }
    except Exception as e:
        return {"error": str(e)}

def check_linkedin():
    """Check LinkedIn — limited read access, but log what we posted"""
    # LinkedIn API can't read our own posts back (403 on read)
    # Return the known posted data
    return {
        "posts_published": 3,
        "note": "LinkedIn API does not allow programmatic readback of own posts"
    }

def check_genviral():
    """Check if Genviral is configured"""
    gk = os.environ.get("GENVIRAL_API_KEY", "")
    if gk:
        return {"configured": True, "note": "API key present — run setup to activate"}
    return {"configured": False, "note": "Genviral skill installed, no API key yet"}

def generate_report():
    now = datetime.datetime.utcnow().isoformat() + "Z"
    data = load_log()
    
    results = {
        "timestamp": now,
        "moltbook": check_moltbook(),
        "linkedin": check_linkedin(),
        "genviral": check_genviral(),
    }
    
    # Calculate summary
    platforms_ok = sum(1 for k, v in results.items() if "error" not in v)
    total_engagement = 0
    if "moltbook" in results and "total_upvotes" in results["moltbook"]:
        total_engagement += results["moltbook"]["total_upvotes"]
    if "moltbook" in results and "total_comments" in results["moltbook"]:
        total_engagement += results["moltbook"]["total_comments"]
    
    results["summary"] = {
        "platforms_tracked": len(results),
        "platforms_ok": platforms_ok,
        "total_posts_live": 6,  # 3 LinkedIn + 3 Moltbook
        "total_engagement": total_engagement,
        "genviral_ready": results.get("genviral", {}).get("configured", False)
    }
    
    data["latest"] = results
    data["history"].append({
        "timestamp": now,
        "summary": results["summary"]
    })
    
    save_log(data)
    
    # Generate dashboard JSON
    with open(DASHBOARD, "w") as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    report = generate_report()
    s = report["summary"]
    print(f"=== Social Engagement Report ===")
    print(f"Time: {report['timestamp']}")
    print(f"Posts live: {s['total_posts_live']}")
    print(f"Total engagement: {s['total_engagement']}")
    print(f"Platforms OK: {s['platforms_ok']}/{s['platforms_tracked']}")
    print(f"Genviral ready: {s['genviral_ready']}")
    
    for platform, data in report.items():
        if platform in ("summary", "timestamp"):
            continue
        print(f"\n--- {platform.upper()} ---")
        for k, v in data.items():
            if k != "posts":
                print(f"  {k}: {v}")
        if "posts" in data:
            for p in data["posts"]:
                print(f"  📄 {p['title']} — {p['upvotes']}👍 {p['comments']}💬 ({p['submolt']})")
                if p.get("spam"):
                    print(f"     ⚠️ Flagged as spam")
