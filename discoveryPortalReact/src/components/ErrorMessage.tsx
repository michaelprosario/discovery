import { ApiError } from '../api/client';

/** Renders an error (ApiError or generic) as a dismissable alert box. */
export function ErrorMessage({ error }: { error: unknown }) {
  if (!error) return null;
  let message = 'Something went wrong.';
  if (error instanceof ApiError) message = error.message;
  else if (error instanceof Error) message = error.message;
  else if (typeof error === 'string') message = error;
  return <div className="alert alert-error">{message}</div>;
}
