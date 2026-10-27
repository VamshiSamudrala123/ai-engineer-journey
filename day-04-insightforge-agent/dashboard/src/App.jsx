import { useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import ReactMarkdown from 'react-markdown'
import {
  Activity, ArrowDownLeft, ArrowRight, ArrowUpRight,
  ArrowUpRight as Outbound, BarChart3, Check, ChevronDown,
  Database, Fingerprint, Globe2, LayoutDashboard,
  FileDown, LockKeyhole, Search, ShieldCheck, Sparkles, WalletCards, Zap,
} from 'lucide-react'

// Verified synthetic dataset snapshot. These are static preview values,
// not a live API connection. We connect the Python backend in the next stage.
const dataset = {
  transactions: 5078345,
  accounts: 518581,
  labels: 5177,
  currencies: 15,
  sendingBankValues: 30528,
  firstDate: '01 Sep 2022',
  lastDate: '18 Sep 2022',
}

const payments = [
  { format: 'Cheque', currency: 'USD', count: 708957, labels: 120, rate: 0.017 },
  { format: 'Credit card', currency: 'USD', count: 506535, labels: 90, rate: 0.018 },
  { format: 'Cheque', currency: 'EUR', count: 441177, labels: 91, rate: 0.021 },
  { format: 'Credit card', currency: 'EUR', count: 315559, labels: 52, rate: 0.016 },
  { format: 'ACH', currency: 'USD', count: 240028, labels: 1663, rate: 0.693 },
  { format: 'Cash', currency: 'USD', count: 187884, labels: 39, rate: 0.021 },
  { format: 'Reinvestment', currency: 'USD', count: 186391, labels: 0, rate: 0 },
  { format: 'Bitcoin', currency: 'BTC', count: 146013, labels: 56, rate: 0.038 },
  { format: 'ACH', currency: 'EUR', count: 140956, labels: 1206, rate: 0.856 },
  { format: 'Reinvestment', currency: 'EUR', count: 116658, labels: 0, rate: 0 },
]

const fmt = n => new Intl.NumberFormat('en-US').format(n)
const nav = [
  { id: 'overview', label: 'Overview', Icon: LayoutDashboard },
  { id: 'payments', label: 'Payment analysis', Icon: BarChart3 },
  { id: 'accounts', label: 'Account investigation', Icon: WalletCards },
  { id: 'assistant', label: 'AI intelligence', Icon: Sparkles },
]

const easing = [0.22, 1, 0.36, 1]
const fadeUp = { initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -8 } }

function BrandMark() {
  return <div className="brand-mark" aria-hidden="true"><span className="mark-core">✳</span></div>
}

function Sidebar({ active, setActive }) {
  return (
    <aside className="sidebar">
      <div className="brand" onClick={() => setActive('overview')} role="button" tabIndex={0} onKeyDown={e => e.key === 'Enter' && setActive('overview')}>
        <BrandMark />
        <div className="brand-type"><strong>InsightForge</strong><span>INTELLIGENCE PLATFORM</span></div>
      </div>
      <div className="sidebar-label">WORKSPACE</div>
      <nav className="side-nav" aria-label="Main navigation">
        {nav.map(({ id, label, Icon }) => (
          <button key={id} className={`nav-link ${active === id ? 'active' : ''}`} aria-label={label} onClick={() => setActive(id)} aria-current={active === id ? 'page' : undefined}>
            <Icon size={18} strokeWidth={1.8} /><span>{label}</span>{active === id && <span className="nav-dot" />}
          </button>
        ))}
      </nav>
      <div className="sidebar-spacer" />
      <div className="sidebar-note">
        <div className="note-icon"><ShieldCheck size={18} /></div>
        <strong>Built with clarity.</strong>
        <p>Explore banking patterns with traceable, synthetic data.</p>
        <span className="note-status"><span className="status-dot" /> Local workspace</span>
      </div>
      <div className="sidebar-footer"><div className="avatar">IF</div><div><strong>InsightForge</strong><span>Developer workspace</span></div><ChevronDown size={15} /></div>
    </aside>
  )
}

function Header({ active }) {
  const current = nav.find(item => item.id === active)
  return (
    <header className="topbar">
      <div className="breadcrumb"><span>Workspace</span><span className="slash">/</span><strong>{current?.label}</strong></div>
      <div className="topbar-right"><span className="preview-label"><span className="status-dot" /> SYNTHETIC DATA</span><span className="topbar-divider" /><div className="header-avatar">IF</div></div>
    </header>
  )
}

function SectionTitle({ kicker, title, subtitle, side }) {
  return <div className="section-title"><div><div className="eyebrow">{kicker}</div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{side}</div>
}

function MetricCard({ icon: Icon, eyebrow, value, sub, variant, delay = 0, reduceMotion }) {
  return <motion.div className={`metric-card ${variant || ''}`} initial={reduceMotion ? false : { opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .6, delay, ease: easing }}>
    <div className="metric-top"><span className="metric-label">{eyebrow}</span><span className="metric-icon"><Icon size={19} strokeWidth={1.65} /></span></div>
    <div className="metric-value">{value}</div><div className="metric-sub">{sub}</div>
  </motion.div>
}


function MetricGrid({ reduceMotion }) {
  const [overview, setOverview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    async function loadOverview() {
      try {
        const response = await fetch('/api/overview', {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`)
        }

        const data = await response.json()

        setOverview(data)
        setError('')
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(
            'Unable to load live data. Check that FastAPI is running.'
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    loadOverview()

    return () => controller.abort()
  }, [])

  const displayValue = (field) => {
    if (loading) return '···'
    if (!overview) return '—'
    return fmt(overview[field])
  }

  const statusText = loading
    ? 'Loading live data…'
    : error
      ? 'Connection unavailable'
      : 'Live · DuckDB'

  const labelRate = overview
    ? (
        overview.laundering_label_count /
        overview.transaction_count *
        100
      ).toFixed(3)
    : null

  return (
    <>
      <div className="metric-grid">
        <MetricCard
          icon={Activity}
          eyebrow="Transactions"
          value={displayValue('transaction_count')}
          sub={statusText}
          delay={0.08}
          reduceMotion={reduceMotion}
        />

        <MetricCard
          icon={WalletCards}
          eyebrow="Accounts"
          value={displayValue('account_count')}
          sub={statusText}
          delay={0.14}
          reduceMotion={reduceMotion}
        />

        <MetricCard
          icon={Fingerprint}
          eyebrow="Labeled transactions"
          value={displayValue('laundering_label_count')}
          sub={
            labelRate
              ? `${labelRate}% of transactions · Live`
              : statusText
          }
          delay={0.20}
          reduceMotion={reduceMotion}
        />

        <MetricCard
          icon={Globe2}
          eyebrow="Currencies"
          value={displayValue('payment_currency_count')}
          sub={statusText}
          delay={0.26}
          reduceMotion={reduceMotion}
          variant="emphasis"
        />
      </div>

      {error && (
        <div className="page-footnote" role="alert">
          <ShieldCheck size={15} />
          {error}
        </div>
      )}
    </>
  )
}


function Hero({ onExplore, reduceMotion }) {
  return <motion.section className="hero" initial={reduceMotion ? false : { opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .7, ease: easing }}>
    <div className="hero-art glow-one" /><div className="hero-art glow-two" />
    <div className="hero-copy">
      <span className="hero-kicker"><span className="star">✳</span> THE BANKING INTELLIGENCE WORKSPACE</span>
      <h1>Complex data.<br /><span>Beautifully clear.</span></h1>
      <p>A thoughtful space to understand transactions, discover patterns, and investigate with AI-powered clarity.</p>
      <button className="primary-btn" onClick={onExplore}>Explore insights <ArrowUpRight size={18} /></button>
    </div>
    <div className="hero-visual" aria-hidden="true">
      <div className="floating-orbit orbit-outer" /><div className="floating-orbit orbit-inner" />
      <div className="glass-chip glass-top"><span className="chip-icon blue"><Activity size={16}/></span><span><b>Data connected</b><small>Synthetic dataset</small></span><Check size={15} className="chip-check"/></div>
      <div className="visual-core"><div className="core-inner"><span>✳</span></div></div>
      <div className="glass-chip glass-bottom"><span className="chip-icon violet"><BarChart3 size={16}/></span><span><b>3 banking tools</b><small>Ready to investigate</small></span><span className="signal-bars"><i/><i/><i/></span></div>
      <div className="orb orb-a"/><div className="orb orb-b"/><div className="orb orb-c"/>
    </div>
  </motion.section>
}

function Segment({ value, onChange }) {
  return <div className="segmented" role="group" aria-label="Chart measure"><button className={value === 'volume' ? 'selected' : ''} onClick={() => onChange('volume')}>Volume</button><button className={value === 'rate' ? 'selected' : ''} onClick={() => onChange('rate')}>Label rate</button></div>
}


function PaymentChart({ compact = false }) {
  const [measure, setMeasure] = useState('volume')
  const [query, setQuery] = useState('')
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    async function loadPayments() {
      try {
        const response = await fetch('/api/payments', {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`)
        }

        const data = await response.json()

        if (!Array.isArray(data)) {
          throw new Error('Unexpected payment response')
        }

        setPayments(data)
        setError('')
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            'Could not load payment data. Check the Python API.'
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    loadPayments()

    return () => controller.abort()
  }, [])

  const sorted = useMemo(() => {
    return [...payments]
      .filter(item =>
        `${item.payment_format} ${item.currency}`
          .toLowerCase()
          .includes(query.toLowerCase())
      )
      .sort((a, b) =>
        measure === 'volume'
          ? b.transaction_count - a.transaction_count
          : b.labeled_percentage - a.labeled_percentage
      )
  }, [payments, measure, query])

  const visible = compact ? sorted.slice(0, 6) : sorted

  const getValue = item =>
    measure === 'volume'
      ? item.transaction_count
      : item.labeled_percentage

  const max = Math.max(
    ...sorted.map(getValue),
    0.001
  )

  return (
    <div className="surface chart-card">
      <div className="card-heading">
        <div>
          <span className="overline">
            TRANSACTION PATTERNS
          </span>
          <h3>Payment landscape</h3>
          <p>
            {compact
              ? 'Explore payment activity across the dataset.'
              : 'Top 10 payment-format and currency groups from DuckDB.'}
          </p>
        </div>
      </div>

      <div className="chart-toolbar">
        <Segment
          value={measure}
          onChange={setMeasure}
        />

        {!compact && (
          <label className="search-field">
            <Search size={15} />
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Filter groups"
              aria-label="Filter payment groups"
            />
          </label>
        )}
      </div>

      <div
        className="bar-chart"
        aria-label={`Payment ${measure} chart`}
        aria-busy={loading}
      >
        {loading ? (
          Array.from(
            { length: compact ? 6 : 10 },
            (_, index) => (
              <div
                className="bar-row"
                key={index}
                aria-hidden="true"
              >
                <div className="bar-label">
                  <span
                    className="insight-skeleton"
                    style={{
                      width: '70%',
                      height: 13,
                      display: 'block',
                    }}
                  />
                </div>

                <div className="bar-track">
                  <div
                    className="insight-skeleton"
                    style={{
                      width: `${90 - index * 7}%`,
                      height: '100%',
                    }}
                  />
                </div>

                <span className="bar-value">
                  <span
                    className="insight-skeleton"
                    style={{
                      width: 52,
                      height: 13,
                      display: 'inline-block',
                    }}
                  />
                </span>
              </div>
            )
          )
        ) : error ? (
          <div className="empty-search" role="alert">
            {error}
          </div>
        ) : visible.length ? (
          visible.map(item => {
            const amount = getValue(item)
            const width = amount === 0
              ? 0
              : Math.max(1, amount / max * 100)

            return (
              <div
                className="bar-row"
                key={`${item.payment_format}-${item.currency}`}
              >
                <div className="bar-label">
                  <span>{item.payment_format}</span>
                  <small>{item.currency}</small>
                </div>

                <div className="bar-track">
                  <motion.div
                    layout
                    initial={{ width: 0 }}
                    animate={{ width: `${width}%` }}
                    transition={{
                      type: 'spring',
                      stiffness: 230,
                      damping: 29,
                    }}
                    className={`bar-fill ${
                      item.payment_format === 'ACH'
                        ? 'bar-highlight'
                        : ''
                    }`}
                  />
                </div>

                <span className="bar-value">
                  {measure === 'volume'
                    ? fmt(item.transaction_count)
                    : `${item.labeled_percentage.toFixed(3)}%`}
                </span>
              </div>
            )
          })
        ) : (
          <div className="empty-search">
            No matching payment groups.
          </div>
        )}
      </div>

      <div className="chart-foot">
        <span>
          <i className="legend-dot" />
          {error
            ? 'Connection unavailable'
            : loading
              ? 'Loading live data'
              : 'Live · DuckDB'}
        </span>

        <span>
          <i className="legend-dot blue" />
          ACH highlighted
        </span>
      </div>
    </div>
  )
}

function AccountSnapshot({ onExplore }) {
  return <div className="surface account-card"><div className="card-heading"><div><span className="overline">ACCOUNT SPOTLIGHT</span><h3>Follow the flow.</h3><p>A featured example from the synthetic dataset.</p></div><span className="circle-action"><ArrowUpRight size={18}/></span></div>
    <div className="account-identity"><span className="account-avatar"><WalletCards size={22} /></span><div><strong>8000F4580</strong><span>Bank 3208</span></div><span className="synthetic-tag">Synthetic</span></div>
    <div className="account-flow"><div className="flow-stat"><span className="circle-icon"><ArrowDownLeft size={17}/></span><strong>0</strong><span>Incoming</span></div><div className="flow-rule"><span/><span/><span/></div><div className="flow-stat"><span className="circle-icon light"><Outbound size={17}/></span><strong>3</strong><span>Outgoing</span></div></div>
    <div className="account-bottom"><span><ShieldCheck size={16}/> 0 synthetic labels</span><button onClick={onExplore}>View investigation <ArrowRight size={15}/></button></div>
  </div>
}

function InsightNote() {
  return <div className="insight-strip"><span className="insight-bubble"><Sparkles size={19}/></span><div><strong>A pattern worth exploring</strong><p>ACH groups in EUR and USD have higher synthetic label percentages than cheque or credit card groups in this snapshot. These labels are not evidence of real-world wrongdoing.</p></div><span className="insight-mark">INSIGHT 01</span></div>
}

function Overview({ go, reduceMotion }) {
  return <div className="page page-overview">
    <Hero onExplore={() => go('payments')} reduceMotion={reduceMotion}/>
    <div className="section-gap"><SectionTitle kicker="AT A GLANCE" title="Your data, in perspective." subtitle="A verified snapshot of the synthetic IBM AML dataset." /></div>
    <MetricGrid reduceMotion={reduceMotion}/>
    <div className="analysis-grid"><PaymentChart compact/><AccountSnapshot onExplore={() => go('accounts')}/></div>
    <InsightNote />
    <div className="page-footnote"><ShieldCheck size={15}/> Overview metrics and payment charts use live DuckDB queries. The featured account is a static example; use Account Investigation for live account lookups.</div>
  </div>
}

function Payments() {
  return <div className="page detail-page">
    <SectionTitle kicker="PAYMENT INTELLIGENCE" title="Understand every pattern." subtitle="Compare transaction volumes and synthetic label rates across payment groups." side={<span className="date-pill"><Database size={15}/> 10 verified groups</span>}/>
    <div className="focus-banner"><div className="focus-icon"><Zap size={23}/></div><div><strong>Where synthetic labels concentrate</strong><p>ACH · EUR shows 0.856% labeled transactions; ACH · USD shows 0.693%. Compare against other groups using the switch below.</p></div><div className="focus-number">0.856%<span>ACH · EUR</span></div></div>
    <PaymentChart />
    <div className="disclaimer"><ShieldCheck size={17}/><span>Label percentages are based on generated data. They do not represent real-world fraud probabilities and must not be compared across currencies as monetary amounts.</span></div>
  </div>
}


function Accounts() {
  const [bankId, setBankId] = useState('3208')
  const [accountNumber, setAccountNumber] = useState('8000F4580')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [reportLoading, setReportLoading] = useState(false)
  const [reportError, setReportError] = useState('')
  const reduceMotion = useReducedMotion()

  async function investigate(event) {
    event.preventDefault()

    if (loading) return

    const bank = bankId.trim()
    const account = accountNumber.trim()

    if (
      !/^\d+$/.test(bank) ||
      !Number.isSafeInteger(Number(bank))
    ) {
      setError('Enter a valid nonnegative numeric bank ID.')
      setResult(null)
      return
    }

    if (!account || account.length > 64) {
      setError('Enter an account number of up to 64 characters.')
      setResult(null)
      return
    }

    setLoading(true)
    setError('')
    setReportError('')
    setResult(null)

    try {
      const response = await fetch('/api/accounts/investigate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          bank_id: Number(bank),
          account_number: account,
        }),
      })

      if (!response.ok) {
        if (response.status === 422) {
          throw new Error('Check the account details and try again.')
        }

        if (response.status === 503) {
          throw new Error('The banking dataset is unavailable.')
        }

        throw new Error('Could not complete the investigation.')
      }

      const data = await response.json()

      if (
        typeof data.total_transactions !== 'number' ||
        typeof data.incoming_transactions !== 'number' ||
        typeof data.outgoing_transactions !== 'number'
      ) {
        throw new Error('The server returned unexpected account data.')
      }

      setResult(data)
    } catch (err) {
      setError(
        err.message || 'Unable to connect to the banking API.'
      )
    } finally {
      setLoading(false)
    }
  }

  async function downloadReport() {
    if (!result || reportLoading || loading) return

    setReportLoading(true)
    setReportError('')

    try {
      // Export the most recently investigated account, not unsaved form edits.
      const response = await fetch('/api/reports/account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bank_id: result.bank_id,
          account_number: result.account_number,
        }),
      })

      if (!response.ok) {
        if (response.status === 422) {
          throw new Error('Invalid account details. Investigate again.')
        }
        if (response.status === 503) {
          throw new Error('Banking dataset is unavailable on the server.')
        }
        throw new Error('Unable to generate the PDF report. Try again.')
      }

      if (!response.headers.get('content-type')?.includes('application/pdf')) {
        throw new Error('The server did not return a valid PDF response.')
      }

      const blob = await response.blob()
      if (blob.size === 0) {
        throw new Error('The PDF report was empty. Please retry.')
      }

      const filenameAccount = String(result.account_number)
        .replace(/[^A-Za-z0-9_-]/g, '_')
        .slice(0, 64) || 'account'
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `InsightForge-Account-${filenameAccount}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) {
      setReportError(
        err instanceof TypeError
          ? 'Cannot connect to FastAPI. Check that your Python server is running.'
          : (err.message || 'Could not download the report.')
      )
    } finally {
      setReportLoading(false)
    }
  }

  return (
    <div className="page detail-page">
      <SectionTitle
        kicker="ACCOUNT INTELLIGENCE"
        title="Know the details."
        subtitle="Investigate account activity with precision and clarity."
        side={
          <span className="date-pill">
            <Database size={15} />
            Live · DuckDB
          </span>
        }
      />

      <section className="surface account-search">
        <div className="account-search-intro">
          <div>
            <span className="overline">ACCOUNT INVESTIGATION</span>
            <h3>Find the full picture.</h3>
            <p>
              Enter a bank identifier and account number to
              investigate transactions in the synthetic dataset.
            </p>
          </div>

          <span className="account-search-icon">
            <Search size={22} />
          </span>
        </div>

        <form className="account-search-form" onSubmit={investigate}>
          <div className="account-field">
            <label htmlFor="bank-id">Bank ID</label>
            <input
              id="bank-id"
              type="text"
              inputMode="numeric"
              placeholder="e.g. 3208"
              value={bankId}
              disabled={loading}
              onChange={e => setBankId(e.target.value)}
              required
            />
          </div>

          <div className="account-field">
            <label htmlFor="account-number">Account number</label>
            <input
              id="account-number"
              type="text"
              placeholder="Enter account number"
              value={accountNumber}
              disabled={loading}
              maxLength={64}
              onChange={e => setAccountNumber(e.target.value)}
              required
            />
          </div>

          <button
            className="account-search-button"
            type="submit"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="account-spinner" />
                Investigating
              </>
            ) : (
              <>
                Investigate
                <ArrowRight size={17} />
              </>
            )}
          </button>
        </form>
      </section>

      {error && (
        <div className="account-message account-error" role="alert">
          <ShieldCheck size={18} />
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div
          className="surface account-loading"
          role="status"
          aria-live="polite"
        >
          <span className="account-spinner" />
          <div>
            <strong>Analyzing transactions</strong>
            <p>Querying the synthetic banking dataset through DuckDB.</p>
          </div>
        </div>
      )}

      {!result && !loading && !error && (
        <div className="account-empty-state">
          <div className="account-empty-symbol">✳</div>
          <h3>Every account tells a story.</h3>
          <p>
            The sample account is prefilled.
            Select Investigate to explore its real transaction activity.
          </p>
        </div>
      )}

      {result && !loading && (
        <motion.div
          className="account-results"
          initial={reduceMotion ? false : { opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easing }}
        >
          <div className="account-hero surface">
            <div className="account-hero-head">
              <span className="overline">
                LIVE INVESTIGATION RESULTS
              </span>
              <span className="synthetic-tag">
                Synthetic data
              </span>
            </div>

            <div className="account-hero-body">
              <div className="large-account-icon">
                <WalletCards size={33} />
              </div>

              <div>
                <span>Account number</span>
                <h2>{result.account_number}</h2>
                <p>Bank identifier: {result.bank_id}</p>
              </div>
            </div>

            <div className="account-stats">
              <div>
                <span>Total transactions</span>
                <strong>{fmt(result.total_transactions)}</strong>
              </div>

              <div>
                <span>Outgoing</span>
                <strong>{fmt(result.outgoing_transactions)}</strong>
              </div>

              <div>
                <span>Incoming</span>
                <strong>{fmt(result.incoming_transactions)}</strong>
              </div>

              <div>
                <span>Self-transfers</span>
                <strong>{fmt(result.self_transfers)}</strong>
              </div>
            </div>
          </div>

          <div className="account-insight surface">
            <span className="account-insight-icon">
              <ShieldCheck size={21} />
            </span>

            <div>
              <strong>
                {result.total_transactions === 0
                  ? 'No matching transactions found'
                  : `${fmt(result.labeled_transactions)} synthetic laundering labels`}
              </strong>

              <p>
                {result.total_transactions === 0
                  ? 'No transactions matched this bank and account combination in the available dataset. This does not establish whether the account exists elsewhere.'
                  : 'These counts reflect the available synthetic transaction records. Labels are not proof of real-world criminal activity, and zero labels do not establish that an account is safe.'}
              </p>
            </div>
          </div>
          <div className="account-report-actions surface">
            <div className="account-report-copy">
              <strong>Download investigation report</strong>
              <p>Evidence-backed PDF · Synthetic data only</p>
            </div>
            <button
              type="button"
              className="account-report-button"
              onClick={downloadReport}
              disabled={reportLoading}
            >
              {reportLoading ? (
                <>
                  <span className="account-spinner" />
                  Generating PDF…
                </>
              ) : (
                <>
                  Download PDF
                  <FileDown size={17} />
                </>
              )}
            </button>
          </div>

          {reportError && (
            <div className="account-message account-error" role="alert">
              <ShieldCheck size={18} />
              <span>{reportError}</span>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}

const suggestions = [
  'Summarize the banking dataset',
  'Compare payment label rates',
  'Investigate account 8000F4580 at bank 3208',
]

const TOOL_LABELS = {
  inspect_banking_data: 'Dataset overview',
  analyze_payment_formats: 'Payment analysis',
  investigate_account: 'Account investigation',
}

function Assistant() {
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState([])
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const threadRef = useRef(null)
  const reduceMotion = useReducedMotion()

  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight
    }
  }, [messages, sending])

  function startNewConversation() {
    if (sending) return

    setMessages([])
    setDraft('')
    setError('')
  }

  async function sendMessage(event) {
    event.preventDefault()

    const question = draft.trim()
    if (!question || sending) return

    
    // Keep the six most recent messages within API limits.
    const history = messages
      .slice(-6)
      .map(({ role, text }) => ({
        role,
        text: text.slice(0, 1900),
      }))

    // Show the user's question immediately.
    setMessages(previous => [
      ...previous,
      { role: 'user', text: question },
    ])
    setDraft('')
    setError('')
    setSending(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, history }),
      })

      if (!response.ok) {
        if (response.status === 422) {
          throw new Error(
            'The question was rejected. Check your input and try again.'
          )
        }

        if (response.status === 503) {
          throw new Error(
            'Gemini is not configured. Check the FastAPI server settings.'
          )
        }

        if (response.status === 502) {
          throw new Error(
            'The AI assistant is temporarily unavailable. Please retry.'
          )
        }

        if (response.status === 429) {
          throw new Error(
            'Too many requests. Please retry after a short break.'
          )
        }

        throw new Error(
          `The API returned HTTP ${response.status}. Please try again.`
        )
      }

      // Read the API result before accessing data.answer or data.tool_activity.
      const data = await response.json()

      if (typeof data.answer !== 'string') {
        throw new Error('The server returned an invalid answer.')
      }

      const toolActivity = Array.isArray(data.tool_activity)
        ? data.tool_activity
            .filter(
              item =>
                item &&
                Object.hasOwn(TOOL_LABELS, item.tool) &&
                ['success', 'error'].includes(item.status)
            )
            .slice(0, 6)
        : []

      // Add a single assistant response with its corresponding tool activity.
      setMessages(previous => [
        ...previous,
        {
          role: 'assistant',
          text: data.answer,
          toolActivity,
        },
      ])
    } catch (err) {
      // Restore the question so the user can send it again.
      setDraft(question)

      // Remove the unanswered question from conversation history.
      setMessages(previous => {
        const last = previous[previous.length - 1]

        if (last?.role === 'user' && last.text === question) {
          return previous.slice(0, -1)
        }

        return previous
      })

      setError(
        err instanceof TypeError
          ? 'Cannot connect to FastAPI. Check that the Python server is running.'
          : (err.message || 'Unable to complete your request.')
      )
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="page assistant-page">
      <div className="assistant-header">
        <span className="eyebrow">GEMINI + BANKING TOOLS</span>
        <h1>
          Ask better questions.
          <br />
          <span>Find clearer answers.</span>
        </h1>
        <p>
          Your AI intelligence agent, connected to real synthetic
          banking data.
        </p>
      </div>

      <div className="assistant-window surface">
        <div className="assistant-window-header">
          <span>
            <span className="assistant-dot" />
            InsightForge Assistant
          </span>

          <div className="assistant-header-actions">
            <span className="soon-pill">
              <ShieldCheck size={13} />
              Live · Gemini + DuckDB
            </span>

            <button
              type="button"
              className="assistant-new-chat"
              onClick={startNewConversation}
              disabled={sending || (messages.length === 0 && !draft && !error)}
            >
              New conversation
            </button>
          </div>
        </div>

        {messages.length === 0 ? (
          <div className="assistant-empty">
            <div className="assistant-glyph">✳</div>

            <h2>Intelligence, on demand.</h2>

            <p>
              Investigate payment patterns, explore dataset statistics,
              or ask about individual accounts using approved
              Python banking tools.
            </p>

            <div className="suggestions">
              {suggestions.map(suggestion => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => setDraft(suggestion)}
                >
                  {suggestion}
                  <ArrowUpRight size={15} />
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div
            className="assistant-thread"
            ref={threadRef}
            aria-live="polite"
          >
            {messages.map((message, index) => (
              <motion.div
                key={index}
                className={`assistant-message ${message.role}`}
                initial={
                  reduceMotion
                    ? false
                    : { opacity: 0, y: 10 }
                }
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <span className="assistant-message-label">
                  {message.role === 'user'
                    ? 'You'
                    : '✳ InsightForge AI'}
                </span>
                
  <div className="assistant-bubble">
  {message.role === 'assistant' ? (
    <>
      <ReactMarkdown>
        {message.text}
      </ReactMarkdown>

      {message.toolActivity?.length > 0 && (
        <div className="assistant-tool-activity">
          <div className="assistant-tool-heading">
            <Database size={14} />
            <span>Tools used</span>
          </div>

          <div className="assistant-tool-list">
            {message.toolActivity.map((item, index) => (
              <span
                key={`${item.tool}-${index}`}
                className={`assistant-tool-pill ${item.status}`}
              >
                {item.status === 'success' && (
                  <Check size={12} />
                )}

                {TOOL_LABELS[item.tool]}

                {item.status === 'error' && (
                  <span> · Error</span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}
    </>
  ) : (
    <p>{message.text}</p>
  )}
</div>

              </motion.div>
            ))}

            {sending && (
              <div className="assistant-message assistant">
                <span className="assistant-message-label">
                  ✳ InsightForge AI
                </span>

                <div className="assistant-bubble assistant-thinking">
                  <span className="account-spinner" />
                  Investigating your question…
                </div>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="assistant-chat-error" role="alert">
            {error}
          </div>
        )}

        <form
          className="assistant-composer"
          onSubmit={sendMessage}
        >
          <input
            aria-label="Ask an investigation question"
            value={draft}
            onChange={event => setDraft(event.target.value)}
            placeholder="Ask a banking question…"
            maxLength={2000}
            disabled={sending}
            required
          />

          <button
            type="submit"
            aria-label="Send message"
            disabled={sending || !draft.trim()}
          >
            <ArrowUpRight size={19} />
          </button>
        </form>

        <p className="composer-caption">
          <LockKeyhole size={13} />
          Gemini key stays on your Python server.
          Follow-up questions use recent conversation context.
          Synthetic data only.
        </p>
      </div>
    </div>
  )
}


export default function App() {
  const [active, setActive] = useState('overview')
  const reduceMotion = useReducedMotion()
  function changePage(page) { setActive(page); window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' }) }
  return <div className="app-shell"><Sidebar active={active} setActive={changePage}/><div className="main-shell"><Header active={active}/><main><AnimatePresence mode="wait"><motion.div key={active} {...(reduceMotion ? {} : fadeUp)} transition={{ duration: .42, ease: easing }}>
    {active === 'overview' && <Overview go={changePage} reduceMotion={reduceMotion} />}
    {active === 'payments' && <Payments/>}
    {active === 'accounts' && <Accounts/>}
    {active === 'assistant' && <Assistant/>}
  </motion.div></AnimatePresence></main><footer className="footer"><span>InsightForge <span className="footer-spark">✳</span> Banking intelligence, beautifully clear.</span><span>Synthetic data only · Local development</span></footer></div></div>
}
