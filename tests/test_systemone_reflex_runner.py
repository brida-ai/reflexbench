import unittest

from systemone_reflex_runner import source_row_metadata


class SystemOneReflexRunnerMetadataTest(unittest.TestCase):
    def test_legacy_metadata_remains_compatible(self):
        got=source_row_metadata({'caseId':'old-1','difficulty':'fixture'},0)
        self.assertEqual(got,{
            'case_id':'old-1','difficulty':'fixture',
            'language':'unspecified','evidence_class':'unspecified',
        })

    def test_core_v1_gate_metadata_is_normalized_without_payload_change(self):
        row={
            'id':'new-1','caseClass':'boundary','language':'es',
            'evidenceClass':'blind_synthetic_workflow',
            'state':{'x':1},
        }
        before=dict(row)
        got=source_row_metadata(row,7)
        self.assertEqual(got,{
            'case_id':'new-1','difficulty':'boundary','language':'es',
            'evidence_class':'blind_synthetic_workflow',
        })
        self.assertEqual(row,before)

    def test_index_is_last_resort_case_identity(self):
        self.assertEqual(source_row_metadata({},3)['case_id'],'3')


class TransportRetryTest(unittest.TestCase):
    def test_retries_retryable_503_and_preserves_ledger(self):
        from systemone_http import HttpResult, SystemOneHttpError
        from systemone_reflex_runner import call_with_transport_retries
        calls=[]
        def fn():
            calls.append(1)
            if len(calls)==1:
                raise SystemOneHttpError(503,'provider unavailable')
            return HttpResult({'answers':{}},1.0,200,{})
        result, meta = call_with_transport_retries(fn,max_retries=2,backoff_ms=0,sleep_fn=lambda _:None)
        self.assertEqual(result.status,200)
        self.assertEqual(meta['attempts'],2)
        self.assertEqual(meta['retries_used'],1)
        self.assertEqual(meta['retry_statuses'],[503])

    def test_does_not_retry_semantic_4xx(self):
        from systemone_http import SystemOneHttpError
        from systemone_reflex_runner import call_with_transport_retries
        calls=[]
        def fn():
            calls.append(1); raise SystemOneHttpError(422,'bad request')
        with self.assertRaises(SystemOneHttpError):
            call_with_transport_retries(fn,max_retries=2,backoff_ms=0,sleep_fn=lambda _:None)
        self.assertEqual(len(calls),1)

    def test_exhausted_retry_keeps_attempt_metadata_on_original_error(self):
        from systemone_http import SystemOneHttpError
        from systemone_reflex_runner import call_with_transport_retries
        def fn(): raise SystemOneHttpError(503,'still unavailable')
        with self.assertRaises(SystemOneHttpError) as ctx:
            call_with_transport_retries(fn,max_retries=2,backoff_ms=0,sleep_fn=lambda _:None)
        self.assertEqual(ctx.exception.reflexbench_transport_meta['attempts'],3)
        self.assertEqual(ctx.exception.reflexbench_transport_meta['retries_used'],2)
        self.assertEqual(ctx.exception.reflexbench_transport_meta['retry_statuses'],[503,503,503])

    def test_retries_connection_error(self):
        from systemone_http import HttpResult
        from systemone_reflex_runner import call_with_transport_retries
        calls=[]
        def fn():
            calls.append(1)
            if len(calls)<3: raise ConnectionError('reset')
            return HttpResult({'answers':{}},1.0,200,{})
        _, meta = call_with_transport_retries(fn,max_retries=2,backoff_ms=0,sleep_fn=lambda _:None)
        self.assertEqual(meta['attempts'],3)
        self.assertEqual(meta['retries_used'],2)
        self.assertEqual(meta['retry_statuses'],[None,None])


if __name__=='__main__': unittest.main()
