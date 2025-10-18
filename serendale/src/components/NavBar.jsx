export default function NavBar() {
  const links = ['Services', 'Case Studies', 'Blogs', 'About Us ', 'Contact Us']
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
