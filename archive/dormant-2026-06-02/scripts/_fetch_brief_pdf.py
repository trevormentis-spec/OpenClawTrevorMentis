#!/usr/bin/env python3
"""
Fetch the latest daily intel brief PDF from Gmail.
Label: "Important Myclaw use this"
Skips messages without PDF attachments (e.g. forwarded copies).

Usage: python3 _fetch_brief_pdf.py /path/to/output.pdf

Requires: MATON_API_KEY in environment
"""
import urllib.request, urllib.parse, json, base64, os, sys

def find_pdf_in_message(msg):
    """Search all parts of a message for a PDF attachment. Returns bytes or None."""
    def search(parts):
        for part in parts:
            if part.get('filename', '').endswith('.pdf'):
                body = part.get('body', {})
                if body.get('data'):
                    return base64.urlsafe_b64decode(body['data'])
                elif body.get('attachmentId'):
                    att_id = body['attachmentId']
                    msg_id = msg['id']
                    url3 = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}/attachments/{att_id}'
                    req3 = urllib.request.Request(url3)
                    req3.add_header('Authorization', f'Bearer {api_key}')
                    try:
                        resp3 = urllib.request.urlopen(req3, timeout=30)
                        att_data = json.loads(resp3.read())
                        if att_data.get('data'):
                            return base64.urlsafe_b64decode(att_data['data'])
                    except Exception:
                        pass
            if part.get('parts'):
                result = search(part['parts'])
                if result:
                    return result
        return None

    # Search from payload top level
    pdf_data = search([msg.get('payload', {})])
    if pdf_data:
        return pdf_data

    # Try inline payload
    body = msg.get('payload', {}).get('body', {})
    filename = msg.get('payload', {}).get('filename', '')
    if body.get('data') and filename.endswith('.pdf'):
        return base64.urlsafe_b64decode(body['data'])

    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: _fetch_brief_pdf.py <output_path>", file=sys.stderr)
        sys.exit(1)

    output_path = sys.argv[1]
    global api_key  # needed by find_pdf_in_message
    api_key = os.environ.get('MATON_API_KEY', '')
    if not api_key:
        print("ERROR: MATON_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    label_query = 'label:important-myclaw-use-this'
    max_to_check = 10

    # Search for messages with the label
    url = 'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages?q=' + \
          urllib.parse.quote(label_query) + f'&maxResults={max_to_check}'
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {api_key}')
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
    except Exception as e:
        print(f'Gmail search failed: {e}', file=sys.stderr)
        sys.exit(1)

    messages = data.get('messages', [])
    if not messages:
        print('No messages found with that label', file=sys.stderr)
        sys.exit(1)

    # Iterate through messages to find one with a PDF
    for m in messages:
        msg_id = m['id']

        # Get full message
        url2 = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}'
        req2 = urllib.request.Request(url2)
        req2.add_header('Authorization', f'Bearer {api_key}')
        try:
            resp2 = urllib.request.urlopen(req2, timeout=30)
            msg = json.loads(resp2.read())
        except Exception as e:
            print(f'Failed to fetch message {msg_id}: {e}', file=sys.stderr)
            continue

        pdf_data = find_pdf_in_message(msg)
        if pdf_data:
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
            print(f'Saved PDF ({len(pdf_data)} bytes) to {output_path}')
            return

    print('No PDF attachment found in any labeled message', file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    main()
