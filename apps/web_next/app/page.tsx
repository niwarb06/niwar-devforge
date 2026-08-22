import { PilotClient } from "./pilot-client";

export default function HomePage() {
  return (
    <main className="shell">
      <section className="card">
        <p className="eyebrow">Niwar DevForge</p>
        <h1>Web authentication browser pilot</h1>
        <p>
          This reference app proves same-origin BFF login/logout and browser session
          revalidation without exposing the backend session token to client JavaScript.
        </p>
        <PilotClient />
      </section>
    </main>
  );
}
