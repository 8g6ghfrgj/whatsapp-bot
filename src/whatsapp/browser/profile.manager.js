import fs from 'fs';
import path from 'path';
import { PATHS } from '../../config/paths.js';

export function getProfilePath(accountId) {
  const profilePath = path.join(
    PATHS.CHROME_DATA,
    'accounts',
    `account_${accountId}`
  );

  if (!fs.existsSync(profilePath)) {
    fs.mkdirSync(profilePath, { recursive: true });
  }

  return profilePath;
}
