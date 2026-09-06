import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Brain, CalendarClock, ShieldCheck, Wallet } from 'lucide-react';
import CinematicScene from '../../components/cinematic/CinematicScene';
import MagneticButton from '../../components/brand/MagneticButton';
import ThemeToggle from '../../components/brand/ThemeToggle';
import { usePointerVars } from '../../hooks/usePointerVars';
import styles from './Landing.module.css';

const FEATURES = [
  {
    icon: Wallet,
    title: 'Unified payroll',
    copy: 'Salary runs, payslips, and compliance land in one ledger — ready before payday.',
    image: '/brand/illo-payroll.png',
    alt: 'Specialist reviewing a digital salary summary',
  },
  {
    icon: CalendarClock,
    title: 'Attendance & leave',
    copy: 'Shifts, due dates, and time-off requests stay visible so nothing slips the cycle.',
    image: '/brand/illo-schedule.png',
    alt: 'Calendar and payroll schedule',
  },
  {
    icon: Brain,
    title: 'AI performance',
    copy: 'Local analytics read the numbers so HR can coach people, not chase spreadsheets.',
    image: '/brand/illo-profile.png',
    alt: 'Employee compensation profile',
  },
  {
    icon: ShieldCheck,
    title: 'Role-based trust',
    copy: 'Admin, HR, and employees each see the orbit they need — and nothing they should not.',
    image: '/brand/illo-meeting.png',
    alt: 'HR consultation between two colleagues',
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const pageRef = useRef<HTMLDivElement>(null);
  usePointerVars(pageRef);

  return (
    <div className={styles.page} ref={pageRef}>
      <CinematicScene />

      <header className={styles.nav}>
        <button className={styles.brand} type="button" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <img src="/brand/logo.png" alt="PeoplePay360" className={styles.logo} />
          <span>PeoplePay360</span>
        </button>
        <div className={styles.navActions}>
          <ThemeToggle />
          <MagneticButton className={styles.ghostBtn} type="button" onClick={() => navigate('/login')}>
            Sign In
          </MagneticButton>
          <MagneticButton className={styles.primaryBtn} type="button" onClick={() => navigate('/register')}>
            Get Started
          </MagneticButton>
        </div>
      </header>

      <main>
        <section className={styles.hero}>
          <div className={styles.heroCopy}>
            <h1 className={styles.headline}>
              Manage your workforce
              <span> with intelligent automation.</span>
            </h1>
            <p className={styles.description}>
              PeoplePay360 brings payroll, attendance, leave, and AI-guided performance insights
              into one intelligent HR workspace — so every payday, policy, and person stays in sync.
            </p>
            <div className={styles.ctaRow}>
              <MagneticButton className={styles.primaryBtnLarge} type="button" onClick={() => navigate('/register')}>
                Create Account
                <ArrowRight size={18} />
              </MagneticButton>
              <MagneticButton className={styles.ghostBtnLarge} type="button" onClick={() => navigate('/login')}>
                Sign In to Demo
              </MagneticButton>
            </div>
          </div>
        </section>

        <section className={styles.features}>
          <div className={styles.sectionHead}>
            <p className={styles.kicker}>The platform</p>
            <h2>Every people operation, one gravitational center.</h2>
          </div>
          <div className={styles.featureGrid}>
            {FEATURES.map((feature) => {
              const Icon = feature.icon;
              return (
                <article
                  key={feature.title}
                  className={styles.featureCard}
                  onPointerMove={(event) => {
                    const card = event.currentTarget;
                    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
                    const box = card.getBoundingClientRect();
                    const px = (event.clientX - box.left) / box.width - 0.5;
                    const py = (event.clientY - box.top) / box.height - 0.5;
                    card.style.transform = `perspective(900px) rotateX(${py * -7}deg) rotateY(${px * 8}deg) translateY(-8px)`;
                  }}
                  onPointerLeave={(event) => {
                    event.currentTarget.style.transform = '';
                  }}
                >
                  <div className={styles.featureVisual}>
                    <img src={feature.image} alt={feature.alt} />
                  </div>
                  <div className={styles.featureBody}>
                    <div className={styles.iconMark}>
                      <Icon size={18} />
                    </div>
                    <h3>{feature.title}</h3>
                    <p>{feature.copy}</p>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className={styles.showcase}>
          <div className={styles.showcaseVisual}>
            <img src="/brand/illo-review.png" alt="Manager and employee reviewing a checklist together" />
          </div>
          <div className={styles.showcaseCopy}>
            <p className={styles.kicker}>Built for real teams</p>
            <h2>From first contract to final payslip, the work stays in view.</h2>
            <p>
              PeoplePay360 is the operating layer for employees, HR, and admins — contracts,
              schedules, attendance, leave, payroll, reports, and a local AI agent that reads
              the same source of truth.
            </p>
            <MagneticButton className={styles.primaryBtnLarge} type="button" onClick={() => navigate('/register')}>
              Launch your workspace
              <ArrowRight size={18} />
            </MagneticButton>
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <div className={styles.brand}>
          <img src="/brand/logo.png" alt="" className={styles.logo} />
          <span>PeoplePay360</span>
        </div>
        <p>Intelligent HR &amp; payroll for teams that move fast.</p>
      </footer>
    </div>
  );
}
