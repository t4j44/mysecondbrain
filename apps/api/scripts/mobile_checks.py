"""Run only disposable tests; never inherit a hosted database or provider secret."""
import os
import runpy
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
os.environ.update({
    'ENVIRONMENT':'test','DATABASE_URL':'sqlite+aiosqlite:///:memory:',
    'SUPABASE_URL':'https://mock.supabase.co',
    'SUPABASE_SECRET_KEY':'sb_secret_mock_secret_key_for_testing_only',
    'SUPABASE_SERVICE_ROLE_KEY':'mock_service_role_key_for_testing_only',
    'SUPABASE_JWT_SECRET':'mock_jwt_secret_for_local_pytest_suite_only_32bytes',
    'TOKEN_ENCRYPTION_KEY':'mock_token_encryption_key_for_local_tests',
    'GEMINI_API_KEY':'mock_gemini_key',
})
if sys.argv[1:] == ['benchmark']:
    os.chdir(root)
    runpy.run_path(str(root/'scripts/benchmark_mobile_home.py'),run_name='__main__')
else:
    import pytest
    sys.exit(pytest.main(sys.argv[1:]))
