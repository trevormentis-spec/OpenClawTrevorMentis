// Netlify function: notify-subscriber-signup
// Emails trevor.mentis@gmail.com when someone signs up via the landing page
const https = require('https');

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  try {
    const data = JSON.parse(event.body);
    const { name, email, edition, trial, organization, use_case } = data;

    // Format notification email
    const subject = encodeURIComponent(`New Subscriber: ${name} — ${edition}`);
    const body = encodeURIComponent(
`New Global Security & Intelligence Brief Subscriber

Name:       ${name || 'N/A'}
Email:      ${email}
Edition:    ${edition}
Trial:      ${trial}
Org:        ${organization || 'N/A'}
Use Case:   ${use_case || 'N/A'}
Time:       ${new Date().toISOString()}
`
    );

    // Send via Gmail API through Maton
    const matonKey = process.env.MATON_API_KEY || '';
    const rawEmail = [
      `From: Trevor <trevor.mentis@gmail.com>`,
      `To: Trevor <trevor.mentis@gmail.com>`,
      `Subject: New Subscriber: ${name} — ${edition}`,
      'MIME-Version: 1.0',
      'Content-Type: text/plain; charset="UTF-8"',
      '',
      `New subscriber for the Global Security & Intelligence Brief`,
      '',
      `Name:       ${name || 'N/A'}`,
      `Email:      ${email}`,
      `Edition:    ${edition}`,
      `Trial:      ${trial || 'N/A'}`,
      `Org:        ${organization || 'N/A'}`,
      `Use Case:   ${use_case || 'N/A'}`,
      '',
      `Time:       ${new Date().toISOString()}`,
    ].join('\n');

    const rawB64 = Buffer.from(rawEmail).toString('base64')
      .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    const payload = JSON.stringify({ raw: rawB64 });

    const options = {
      hostname: 'gateway.maton.ai',
      path: '/google-mail/gmail/v1/users/me/messages/send',
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${matonKey}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
      },
    };

    return new Promise((resolve) => {
      const req = https.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => body += chunk);
        res.on('end', () => {
          resolve({
            statusCode: 200,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ok: true, message: 'Subscriber notified' }),
          });
        });
      });
      req.on('error', (err) => {
        resolve({
          statusCode: 200,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ok: true, message: 'Queued (email failed)' }),
        });
      });
      req.write(payload);
      req.end();
    });
  } catch (err) {
    return {
      statusCode: 200,
      body: JSON.stringify({ ok: true }),
    };
  }
};
