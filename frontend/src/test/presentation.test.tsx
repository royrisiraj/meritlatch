import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { CaseState, Ladder, Source, MetricsView, Reasons, AuditList, Message } from '../ui';
import { ApiError } from '../api';
import { validateFile } from '../features/cases';
import type { Case, Metrics } from '../domain';
describe('server state presentation', () => {
  it.each([0, 1, 2, 3])('keeps exact server L%s', level => { render(<Ladder level={level} />); expect(screen.getByLabelText(`Server permission L${level}`)).toBeVisible(); expect(screen.getByText(/current/)).toHaveTextContent(`L${level}`); });
  it.each(['MOCK_AI', 'SYNTHETIC', 'RECORDED_LIVE', 'LIVE_GEMINI'])('labels %s faithfully', value => { render(<Source value={value} />); expect(screen.getByText(`Source: ${value}`)).toBeVisible(); });
  it('does not label absent evidence as live', () => { render(<Source value={null} />); expect(screen.getByText('Source: NO_EVIDENCE')).toBeVisible(); });
  it('separates inspection, business and review', () => { render(<CaseState value={{ provider_mode: 'MOCK_AI', inspection_status: 'SAFETY_ALERT', business_status: 'CORRECTION_REQUIRED', review_state: 'NOT_REVIEWED', max_permission: 1, reason_codes: ['PRESSURE_OUT_OF_RANGE'], available_actions: ['view_case'] } as Case} />); expect(screen.getByText('Inspection: SAFETY_ALERT')).toBeVisible(); expect(screen.getByText('Business: CORRECTION_REQUIRED')).toBeVisible(); expect(screen.getByLabelText('Server permission L1')).toBeVisible(); });
  it('shows binary denominators separately from abstention', () => { render(<MetricsView value={{ false_approvals: 1, false_approval_denominator: 26, false_approval_rate: 1 / 26, false_rejections: 0, false_rejection_denominator: 0, false_rejection_rate: null, review_abstentions: 8 } as Metrics} />); expect(screen.getByText('1/26 — 3.85%')).toBeVisible(); expect(screen.getByText('0/0 — N/A')).toBeVisible(); expect(screen.getByText(/excluded from binary/)).toBeVisible(); });
  it('renders audit events without invented outcomes', () => { render(<AuditList rows={[{ id: 'x', event_type: 'MANAGER_REJECTED_EVIDENCE', created_at: 1, reason_codes: ['CORRECTION_REQUESTED'] }]} />); expect(screen.getByText('MANAGER_REJECTED_EVIDENCE')).toBeVisible(); expect(screen.queryByText('Paid')).not.toBeInTheDocument(); });
  it('does not render arbitrary reason payload as HTML', () => { render(<Reasons codes={['<script>secret</script>']} />); expect(screen.getByText('UNRECOGNIZED_REASON')).toBeVisible(); expect(screen.queryByText(/secret/)).toBeNull(); });
  it.each([401, 403, 404, 409, 429])('provides safe %s error recovery', status => { render(<Message error={new ApiError(status, ['VERSION_CONFLICT'])} />); expect(screen.getByRole('alert')).toHaveTextContent('VERSION_CONFLICT'); });
  it('provides network failure guidance', () => { render(<Message error={new TypeError('secret stack')} />); expect(screen.getByRole('alert')).toHaveTextContent('Connection unavailable'); expect(screen.queryByText('secret stack')).toBeNull(); });
  it.each([['text/html', 1, 'Choose'], ['image/png', 0, 'empty'], ['image/jpeg', 5 * 1024 * 1024 + 1, 'exceeds']])('validates uploads %s', (type, size, message) => { const f = new File(['x'], 'image', { type: String(type) }); Object.defineProperty(f, 'size', { value: size }); expect(validateFile(f)).toContain(message); });
  it('accepts valid bounded PNG for server verification', () => expect(validateFile(new File(['x'], 'a.png', { type: 'image/png' }))).toBeNull());
});
