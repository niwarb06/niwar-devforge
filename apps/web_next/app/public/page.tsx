export default function PublicPage() {
  return (
    <main className="shell">
      <section className="card">
        <p className="eyebrow">Public route</p>
        <h1>History navigation target</h1>
        <p>This page exists so the browser can navigate away and then return to the auth page.</p>
        <a href="/">Return to auth pilot</a>
      </section>
    </main>
  );
}
