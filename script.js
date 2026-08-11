const bootScreen = document.querySelector('#bootScreen');
const enterButton = document.querySelector('#enterButton');
const menuToggle = document.querySelector('.menu-toggle');
const navigation = document.querySelector('.site-nav');
const mainContent = document.querySelector('#mainContent');

const enterPortfolio = () => {
  if (document.body.classList.contains('entered')) return;
  document.body.classList.remove('booting');
  document.body.classList.add('entered');
  enterButton?.blur();
  window.setTimeout(() => bootScreen?.setAttribute('aria-hidden', 'true'), 700);
};

enterButton?.addEventListener('click', enterPortfolio);
window.addEventListener('keydown', (event) => {
  if ((event.code === 'Space' || event.code === 'Enter' || event.code === 'Escape') && !document.body.classList.contains('entered')) {
    event.preventDefault();
    enterPortfolio();
  }
});

menuToggle?.addEventListener('click', () => {
  const isOpen = navigation.classList.toggle('open');
  menuToggle.setAttribute('aria-expanded', String(isOpen));
  menuToggle.querySelector('span').textContent = isOpen ? 'CLOSE' : 'MENU';
});

navigation?.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', () => {
    navigation.classList.remove('open');
    menuToggle?.setAttribute('aria-expanded', 'false');
    if (menuToggle) menuToggle.querySelector('span').textContent = 'MENU';
  });
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { root: mainContent, threshold: 0.12 });
document.querySelectorAll('.reveal').forEach((element) => observer.observe(element));

document.querySelector('#year').textContent = new Date().getFullYear();
document.querySelector('.back-top')?.addEventListener('click', () => mainContent?.scrollTo({ top: 0, behavior: 'smooth' }));

document.querySelectorAll('.channel').forEach((channel) => {
  channel.addEventListener('toggle', () => {
    if (!channel.open) return;
    document.querySelectorAll('.channel[open]').forEach((openChannel) => {
      if (openChannel !== channel) openChannel.open = false;
    });
  });
});

if (window.matchMedia('(hover: hover) and (prefers-reduced-motion: no-preference)').matches) {
  document.querySelectorAll('.magnetic').forEach((card) => {
    card.addEventListener('pointermove', (event) => {
      const bounds = card.getBoundingClientRect();
      const x = (event.clientX - bounds.left) / bounds.width - .5;
      const y = (event.clientY - bounds.top) / bounds.height - .5;
      card.style.transform = `perspective(800px) rotateX(${-y * 2.4}deg) rotateY(${x * 2.4}deg) translateY(-4px)`;
    });
    card.addEventListener('pointerleave', () => { card.style.transform = ''; });
  });
}
