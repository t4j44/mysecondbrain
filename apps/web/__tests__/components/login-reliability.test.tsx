import {act,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {describe,expect,it,vi} from 'vitest';
import Login from '@/app/(auth)/login/page';

const mocks=vi.hoisted(()=>({signIn:vi.fn(),push:vi.fn(),refresh:vi.fn(),toast:vi.fn()}));
vi.mock('next/navigation',()=>({useRouter:()=>({push:mocks.push,refresh:mocks.refresh}),useSearchParams:()=>new URLSearchParams('redirect=/people')}));
vi.mock('@/lib/supabase/client',()=>({createClient:()=>({auth:{signInWithPassword:mocks.signIn}})}));
vi.mock('@/components/shared/google-sign-in',()=>({GoogleSignIn:()=>null}));
vi.mock('@/components/ui/use-toast',()=>({useToast:()=>({toast:mocks.toast})}));

describe('lazy login submission',()=>{
 it('does not sign in until submit, prevents duplicate requests, keeps input after failure and permits retry',async()=>{
  let finish:(value:unknown)=>void=()=>{};
  mocks.signIn.mockReturnValueOnce(new Promise(resolve=>{finish=resolve;}));
  mocks.signIn.mockResolvedValueOnce({error:null});
  render(<Login/>);expect(mocks.signIn).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText('Email Address'),{target:{value:'synthetic@example.invalid'}});
  fireEvent.change(screen.getByLabelText('Password'),{target:{value:'fictional-test-password'}});
  const button=screen.getByRole('button',{name:'Sign in',exact:true});
  fireEvent.submit(button.closest('form')!);fireEvent.submit(button.closest('form')!);
  await waitFor(()=>expect(mocks.signIn).toHaveBeenCalledTimes(1));
  await act(async()=>{finish({error:new Error('Synthetic unavailable')});});
  await waitFor(()=>expect(button).toBeEnabled());
  expect(screen.getByLabelText('Email Address')).toHaveValue('synthetic@example.invalid');
  expect(mocks.push).not.toHaveBeenCalled();expect(mocks.toast).toHaveBeenCalled();
  fireEvent.submit(button.closest('form')!);
  await waitFor(()=>expect(mocks.push).toHaveBeenCalledWith('/people'));
  expect(mocks.signIn).toHaveBeenCalledTimes(2);
 });
});
