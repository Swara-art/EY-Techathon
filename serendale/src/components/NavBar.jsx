export default function NavBar() {
  const links = ['Smart Contracts', 'Services', 'Solutions', 'Roadmap', 'Whitepaper']
  return (
    <header className="nav">
      <div className="container">
        <div className="brand">Serendale</div>
        <nav>
          <ul>
            {links.map((l) => (
              <li key={l}><a href="#">{l}</a></li>
            ))}
          </ul>
        </nav>
        <div className="socials">
          <span aria-hidden>●</span>
          <span aria-hidden>●</span>
          <span aria-hidden>●</span>
        </div>
      </div>
    </header>
  )
}
