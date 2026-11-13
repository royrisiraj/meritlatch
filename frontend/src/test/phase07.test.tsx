import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { CaseState, Ladder, LoadedState, Comparison, TechnicalDetails, Fields, MetricsView } from '../ui';
import { CandidateDetail } from '../features/engineering';
import type { Case, Metrics } from '../domain';

const api = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));
vi.mock('../auth', () => ({ useAuth: () => ({ api, user: { id: 'independent-reviewer', role: 'ENGINEER' } }) }));
beforeEach(() => { api.get.mockReset(); api.post.mockReset(); });
const caseState = (inspection_status = 'SAFETY_ALERT'): Case => ({
  max_permission: 1, provider_mode: 'MOCK_AI', inspection_status,
  business_status: 'CORRECTION_REQUIRED', review_state: 'NOT_REVIEWED',
  reason_codes: ['PRESSURE_OUT_OF_RANGE'], guidance: 'Request qualified safety review.',
  available_actions: ['view_case', 'request_challenge'],
} as Case);

describe('Phase 07 authority and evidence presentation', () => {
  it('moves the current rung downward without marking earlier authority as completed', () => {
    const { rerender } = render(<Ladder level={3} />);
    expect(screen.getByLabelText('Server permission L3').querySelector('[aria-current]')).toHaveTextContent('L3');
    rerender(<Ladder level={1} />);
    const ladder = screen.getByLabelText('Server permission L1');
    expect(ladder.querySelectorAll('[aria-current]')).toHaveLength(1);
    expect(ladder.querySelector('[aria-current]')).toHaveTextContent('L1');
    expect(within(ladder).queryAllByRole('button')).toHaveLength(0);
    expect(within(ladder).queryAllByRole('checkbox')).toHaveLength(0);
    expect(screen.getByText(/Permission can decrease/)).toBeVisible();
    expect(screen.getByText(/role and assignment still govern/)).toBeVisible();
  });

  it('exposes all four meanings and a separate human boundary without payment authority', () => {
    render(<Ladder level={2} />);
    const ladder = screen.getByLabelText('Server permission L2');
    expect(within(ladder).getAllByRole('listitem')).toHaveLength(4);
    for (const text of ['Draft / request evidence', 'Provisional visit', 'Prepare invoice for review', 'Human-approved simulation']) expect(within(ladder).getByText(text)).toBeVisible();
    expect(within(ladder).getByText('Separate authenticated manager approval')).toBeVisible();
    expect(screen.getByText(/L3 permits authorized simulation only/)).toBeVisible();
  });

  it('keeps an unsafe L1 conspicuous and separate from business, review and source', () => {
    render(<CaseState value={caseState()} />);
    expect(screen.getByRole('alert')).toHaveTextContent('Safety restriction');
    expect(screen.getByText('Inspection: SAFETY_ALERT')).toBeVisible();
    expect(screen.getByText('Business: CORRECTION_REQUIRED')).toBeVisible();
    expect(screen.getByText('Review: NOT_REVIEWED')).toBeVisible();
    expect(screen.getByText('Source: MOCK_AI')).toBeVisible();
    expect(screen.getByLabelText('Server permission L1')).toBeVisible();
    expect(screen.getByText('Request qualified safety review.')).toBeVisible();
    expect(screen.queryByText('Source: LIVE_GEMINI')).toBeNull();
  });

  it('does not invent a safety alert when the server reports uncertainty instead', () => {
    render(<CaseState value={caseState('REVIEW_REQUIRED')} />);
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.getByText('Inspection: REVIEW_REQUIRED')).toBeVisible();
  });

  it('distinguishes retained data after refresh failure and clears the notice on success', () => {
    const { rerender } = render(<LoadedState loading={false} error={new Error('private failure')} hasData />);
    expect(screen.getByRole('status')).toHaveTextContent('Previously loaded state');
    expect(screen.getByRole('status')).toHaveTextContent('refresh failed');
    expect(screen.queryByText(/private failure/)).toBeNull();
    rerender(<LoadedState loading error={undefined} hasData />);
    expect(screen.getByRole('status')).toHaveTextContent('refreshing from the server');
    rerender(<LoadedState loading={false} error={undefined} hasData />);
    expect(screen.queryByRole('status')).toBeNull();
  });

  it('does not imply previously loaded authority on the initial load', () => {
    render(<LoadedState loading error={undefined} hasData={false} />);
    expect(screen.getByRole('status')).toHaveTextContent('Loading authorized record');
    expect(screen.queryByText(/Previously loaded state/)).toBeNull();
  });

  it('keeps expected denial and actual allowance in distinct labeled comparison sections', () => {
    render(<Comparison expected={{ decision: 'DENY', max_permission: 1 }} actual={{ decision: 'ALLOW', max_permission: 2 }} />);
    const expected = screen.getByRole('heading', { name: 'Expected' }).closest('section')!;
    const actual = screen.getByRole('heading', { name: 'Actual' }).closest('section')!;
    expect(within(expected).getByText('DENY')).toBeVisible();
    expect(within(actual).getByText('ALLOW')).toBeVisible();
    expect(within(expected).queryByText('ALLOW')).toBeNull();
    expect(within(actual).queryByText('DENY')).toBeNull();
  });

  it('retains a full technical binding behind a native disclosure', async () => {
    const digest = 'a'.repeat(64);
    render(<TechnicalDetails title="Evidence technical binding"><Fields value={{ evidence_sha256: digest, evidence_version: 7 }} /></TechnicalDetails>);
    const summary = screen.getByText('Evidence technical binding');
    expect(summary.tagName).toBe('SUMMARY');
    expect(summary.parentElement?.tagName).toBe('DETAILS');
    expect(summary.parentElement).not.toHaveAttribute('open');
    await userEvent.click(summary);
    expect(summary.parentElement).toHaveAttribute('open');
    expect(screen.getByText(digest)).toBeVisible();
    expect(screen.getByText('7')).toBeVisible();
  });

  it('retains undefined binary rates and separate abstentions in the synthetic report', () => {
    render(<MetricsView value={{ total_expected: 3, total_executed: 3, false_approvals: 0, false_approval_denominator: 0, false_approval_rate: null, false_rejections: 1, false_rejection_denominator: 2, false_rejection_rate: .5, review_abstentions: 1, review_bypasses: 0, unevaluable: 0 } as Metrics} />);
    expect(screen.getByText('Source: SYNTHETIC')).toBeVisible();
    expect(screen.getByText('0/0 — N/A')).toBeVisible();
    expect(screen.getByText('1/2 — 50.00%')).toBeVisible();
    expect(screen.getByText(/SHOULD_DENY/)).toBeVisible();
    expect(screen.getByText(/excluded from binary rate denominators/)).toBeVisible();
  });
});

it.each(['BLOCKED', 'READY_FOR_MANUAL_RELEASE'])('renders authoritative %s separately from publication', async decision => {
  const candidate = { id: 'candidate', profile: 'SAFE_BASELINE', version: 2, review_revision: 1, author_id: 'author', artifact_sha256: 'a'.repeat(64), software_revision: 'revision', current_binding_valid: true, published: false };
  const run = { id: 'run', candidate_id: candidate.id, candidate_version: 2, status: 'COMPLETE', summary: { failed: 0 }, current_binding_valid: true };
  api.get.mockImplementation(async (url: string) => url.endsWith('/history') ? { proposals: [], reviews: [], gates: [] } : url.startsWith('/v1/redteam/runs?') ? { items: [run] } : candidate);
  api.post.mockResolvedValue({ id: 'gate', decision, historical_decision: decision, reason_codes: [], published: false, current_binding_valid: true, candidate_id: candidate.id, candidate_version: 2, artifact_sha256: candidate.artifact_sha256, run_id: run.id, review_id: 'review' });
  render(<MemoryRouter initialEntries={['/engineer/candidates/candidate']}><Routes><Route path="/engineer/candidates/:id" element={<CandidateDetail />} /></Routes></MemoryRouter>);
  await screen.findByRole('button', { name: 'Evaluate release readiness' });
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Gate run' }), 'run');
  await userEvent.click(screen.getByRole('button', { name: 'Evaluate release readiness' }));
  expect(await screen.findByRole('heading', { name: decision })).toBeVisible();
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/v1/redteam/candidates/candidate/release-gate', { expected_version: 2, run_id: 'run', review_id: null }));
  expect(screen.getAllByText('false', { exact: true }).length).toBeGreaterThan(0);
  expect(screen.queryByRole('button', { name: /^Publish/ })).toBeNull();
  expect(screen.queryByRole('heading', { name: 'PUBLISHED' })).toBeNull();
});

