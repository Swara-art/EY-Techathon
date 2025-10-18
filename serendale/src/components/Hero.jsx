
import { Link } from 'react-router-dom'

export default function Hero() {
  return (
    <section className="hero">
      <div className="hero-inner">
  <h1 className="ey-gradient slide-in-left delay-1">AI that Automates Healthcare Directory</h1>
  <h2 className="ey-title slide-in-right delay-2">Scalable AI</h2>
  <p className="ey-sub slide-up delay-3">
          A smart AI system that automatically fixes inaccurate healthcare provider directories, a task that is currently slow, expensive, and manual.

        </p>
        <div className="cta slide-up delay-4" style={{ gap: 16 }}>
          <Link className="pill-btn" to="/get-started">
            <span className="pill-avatar-ring">
              <span className="pill-avatar" />
            </span>
            <span className="pill-text">Get Started</span>

            <span className="pill-arrow" aria-hidden>
              <svg viewBox="0 0 24 24">
                <path d="M6 18 L18 6" />
                <path d="M9 6 H18 V15" />
              </svg>
            </span>
          </Link>
        </div>
      </div>
    </section>
  )
}
