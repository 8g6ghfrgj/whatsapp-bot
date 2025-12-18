// ============================================
// Auth State Manager Module
// Handles WhatsApp authentication state and sessions
// Version: 1.0.0
// ============================================

const { writeFile, readFile, mkdir, stat, unlink } = require('fs').promises;
const { join, dirname } = require('path');
const crypto = require('crypto');

class AuthStateManager {
    constructor(sessionFilePath = './data/auth_info_multi.json') {
        this.sessionFilePath = sessionFilePath;
        this.sessionDir = dirname(sessionFilePath);
        this.backupDir = join(this.sessionDir, 'backups');
        this.state = null;
        this.saveCredsCallback = null;
        this.encryptionKey = process.env.SESSION_ENCRYPTION_KEY || null;
        this.maxBackups = 10;
        this.sessionInfo = {
            created: null,
            lastUsed: null,
            deviceName: 'WhatsApp Companion Bot',
            platform: 'Node.js',
            version: '1.0.0'
        };
        
        console.log('✅ Auth State Manager Initialized');
        console.log(`📁 Session file: ${this.sessionFilePath}`);
    }
    
    /**
     * Initialize authentication directories
     */
    async initDirectories() {
        try {
            await mkdir(this.sessionDir, { recursive: true });
            await mkdir(this.backupDir, { recursive: true });
            console.log(`📁 Auth directories created`);
        } catch (error) {
            console.error('❌ Failed to create auth directories:', error);
        }
    }
    
    /**
     * Load or create authentication state
     * @returns {Promise<Object>} Authentication state and save callback
     */
    async loadAuthState() {
        try {
            await this.initDirectories();
            
            // Try to load existing session
            const loadedState = await this.loadSessionFromFile();
            
            if (loadedState) {
                console.log('✅ Session loaded successfully');
                this.state = loadedState;
                this.updateSessionInfo({ lastUsed: new Date() });
            } else {
                console.log('📝 No existing session found, creating new one');
                this.state = this.createNewAuthState();
                await this.saveSessionToFile();
            }
            
            // Setup save callback
            this.saveCredsCallback = async () => {
                await this.saveSessionToFile();
            };
            
            // Backup old session if exists
            await this.createBackup();
            
            return {
                state: this.state,
                saveCreds: this.saveCredsCallback.bind(this)
            };
            
        } catch (error) {
            console.error('❌ Failed to load auth state:', error);
            return this.createFallbackAuthState();
        }
    }
    
    /**
     * Create new authentication state
     */
    createNewAuthState() {
        const deviceId = `bot-${crypto.randomBytes(4).toString('hex')}`;
        const phoneId = crypto.randomBytes(16).toString('hex');
        const identityId = crypto.randomBytes(20).toString('hex');
        
        const now = Date.now();
        
        this.sessionInfo = {
            ...this.sessionInfo,
            created: new Date(),
            lastUsed: new Date(),
            deviceId: deviceId,
            sessionId: `session_${now}`
        };
        
        return {
            creds: {
                noiseKey: { private: Buffer.alloc(32), public: Buffer.alloc(32) },
                pairingEphemeralKeyPair: { private: Buffer.alloc(32), public: Buffer.alloc(32) },
                signedIdentityKey: { private: Buffer.alloc(32), public: Buffer.alloc(32) },
                signedPreKey: { 
                    keyPair: { private: Buffer.alloc(32), public: Buffer.alloc(32) },
                    signature: Buffer.alloc(64),
                    keyId: 1
                },
                registrationId: 123,
                advSecretKey: crypto.randomBytes(32).toString('base64'),
                processedHistoryMessages: [],
                nextPreKeyId: 1,
                firstUnuploadedPreKeyId: 1,
                accountSyncCounter: 0,
                accountSettings: {
                    unarchiveChats: false
                },
                deviceId: deviceId,
                phoneId: phoneId,
                identityId: identityId,
                me: null,
                account: null,
                signalIdentities: [],
                platform: 'android',
                lastPropHash: null
            },
            keys: {}
        };
    }
    
    /**
     * Load session from file
     */
    async loadSessionFromFile() {
        try {
            const fileExists = await this.fileExists(this.sessionFilePath);
            
            if (!fileExists) {
                return null;
            }
            
            let data = await readFile(this.sessionFilePath, 'utf8');
            
            // Check if data is encrypted
            if (this.isEncryptedData(data)) {
                if (!this.encryptionKey) {
                    console.warn('⚠️ Encrypted session found but no key provided');
                    return null;
                }
                data = await this.decryptData(data);
            }
            
            const parsed = JSON.parse(data);
            this.state = parsed.state || parsed;
            
            // Load session info if exists
            if (parsed.sessionInfo) {
                this.sessionInfo = parsed.sessionInfo;
                this.sessionInfo.lastUsed = new Date();
            }
            
            // Validate session structure
            if (!this.validateSessionStructure(this.state)) {
                console.warn('⚠️ Invalid session structure, creating new one');
                return null;
            }
            
            console.log(`📅 Session created: ${this.sessionInfo.created ? this.sessionInfo.created.toLocaleString() : 'Unknown'}`);
            console.log(`📱 Device ID: ${this.state.creds?.deviceId || 'Unknown'}`);
            
            return this.state;
            
        } catch (error) {
            console.error('❌ Error loading session:', error);
            return null;
        }
    }
    
    /**
     * Save session to file
     */
    async saveSessionToFile() {
        try {
            if (!this.state) {
                console.warn('⚠️ No state to save');
                return false;
            }
            
            // Update session info
            this.sessionInfo.lastUsed = new Date();
            if (!this.sessionInfo.created) {
                this.sessionInfo.created = new Date();
            }
            
            const dataToSave = {
                state: this.state,
                sessionInfo: this.sessionInfo,
                savedAt: new Date().toISOString(),
                version: '1.0.0'
            };
            
            let dataString = JSON.stringify(dataToSave, null, 2);
            
            // Encrypt if key is available
            if (this.encryptionKey) {
                dataString = await this.encryptData(dataString);
            }
            
            await writeFile(this.sessionFilePath, dataString, 'utf8');
            
            // Create backup every 10 saves
            const saveCount = await this.getSaveCount();
            if (saveCount % 10 === 0) {
                await this.createBackup();
            }
            
            console.log(`💾 Session saved at: ${new Date().toLocaleTimeString()}`);
            return true;
            
        } catch (error) {
            console.error('❌ Failed to save session:', error);
            return false;
        }
    }
    
    /**
     * Create backup of current session
     */
    async createBackup() {
        try {
            const fileExists = await this.fileExists(this.sessionFilePath);
            if (!fileExists) return;
            
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const backupPath = join(this.backupDir, `session_backup_${timestamp}.json`);
            
            const data = await readFile(this.sessionFilePath, 'utf8');
            await writeFile(backupPath, data, 'utf8');
            
            // Clean up old backups
            await this.cleanupOldBackups();
            
            console.log(`📦 Session backed up: ${backupPath}`);
            return backupPath;
            
        } catch (error) {
            console.error('❌ Failed to create backup:', error);
        }
    }
    
    /**
     * Clean up old backups
     */
    async cleanupOldBackups() {
        try {
            const files = await readdir(this.backupDir).catch(() => []);
            const backupFiles = files.filter(f => f.startsWith('session_backup_')).sort();
            
            if (backupFiles.length > this.maxBackups) {
                const filesToDelete = backupFiles.slice(0, backupFiles.length - this.maxBackups);
                
                for (const file of filesToDelete) {
                    await unlink(join(this.backupDir, file));
                    console.log(`🗑️  Deleted old backup: ${file}`);
                }
            }
        } catch (error) {
            // Silent fail
        }
    }
    
    /**
     * Clear authentication state (logout)
     */
    async clearAuthState() {
        try {
            // Create final backup before clearing
            await this.createBackup();
            
            // Rename current session file
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const archivedPath = join(this.sessionDir, `session_archived_${timestamp}.json`);
            
            if (await this.fileExists(this.sessionFilePath)) {
                await rename(this.sessionFilePath, archivedPath);
                console.log(`📁 Session archived: ${archivedPath}`);
            }
            
            // Clear state
            this.state = null;
            this.sessionInfo = {
                ...this.sessionInfo,
                created: null,
                lastUsed: null,
                sessionId: null
            };
            
            console.log('✅ Auth state cleared successfully');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to clear auth state:', error);
            return false;
        }
    }
    
    /**
     * Get session information
     */
    getSessionInfo() {
        return {
            ...this.sessionInfo,
            sessionFile: this.sessionFilePath,
            backupDir: this.backupDir,
            hasState: !!this.state,
            isEncrypted: !!this.encryptionKey,
            deviceId: this.state?.creds?.deviceId,
            phoneId: this.state?.creds?.phoneId,
            me: this.state?.creds?.me
        };
    }
    
    /**
     * Update session information
     */
    updateSessionInfo(info) {
        this.sessionInfo = {
            ...this.sessionInfo,
            ...info,
            lastUpdated: new Date()
        };
        
        // Auto-save if state exists
        if (this.state) {
            setTimeout(() => this.saveSessionToFile(), 1000);
        }
    }
    
    /**
     * Update 'me' information (user data)
     */
    async updateUserInfo(userData) {
        if (!this.state) return false;
        
        try {
            this.state.creds.me = userData;
            this.sessionInfo.userName = userData?.name || userData?.id;
            this.sessionInfo.userId = userData?.id;
            
            await this.saveSessionToFile();
            console.log(`👤 User info updated: ${userData?.name || userData?.id}`);
            return true;
            
        } catch (error) {
            console.error('❌ Failed to update user info:', error);
            return false;
        }
    }
    
    /**
     * Check if session exists and is valid
     */
    async hasValidSession() {
        try {
            if (!this.state) return false;
            
            // Check if session file exists
            const fileExists = await this.fileExists(this.sessionFilePath);
            if (!fileExists) return false;
            
            // Check if session is not too old (30 days)
            if (this.sessionInfo.created) {
                const ageInDays = (new Date() - new Date(this.sessionInfo.created)) / (1000 * 60 * 60 * 24);
                if (ageInDays > 30) {
                    console.warn('⚠️ Session is older than 30 days');
                    return false;
                }
            }
            
            // Validate structure
            return this.validateSessionStructure(this.state);
            
        } catch (error) {
            return false;
        }
    }
    
    /**
     * Validate session structure
     */
    validateSessionStructure(session) {
        if (!session) return false;
        if (!session.creds) return false;
        if (!session.creds.deviceId) return false;
        if (!session.creds.phoneId) return false;
        if (!session.creds.identityId) return false;
        
        return true;
    }
    
    /**
     * Get list of all sessions
     */
    async getAllSessions() {
        try {
            const files = await readdir(this.sessionDir).catch(() => []);
            const sessionFiles = files.filter(f => f.endsWith('.json'));
            
            const sessions = [];
            for (const file of sessionFiles) {
                const filePath = join(this.sessionDir, file);
                try {
                    const data = await readFile(filePath, 'utf8');
                    const parsed = JSON.parse(data);
                    
                    sessions.push({
                        file: file,
                        path: filePath,
                        size: (await stat(filePath)).size,
                        created: parsed.sessionInfo?.created || (await stat(filePath)).birthtime,
                        lastUsed: parsed.sessionInfo?.lastUsed,
                        userName: parsed.sessionInfo?.userName,
                        deviceId: parsed.state?.creds?.deviceId,
                        isValid: this.validateSessionStructure(parsed.state || parsed)
                    });
                } catch (e) {
                    // Skip invalid files
                }
            }
            
            return sessions;
            
        } catch (error) {
            console.error('❌ Error getting sessions:', error);
            return [];
        }
    }
    
    /**
     * Switch to different session
     */
    async switchSession(sessionFile) {
        try {
            // Backup current session
            await this.createBackup();
            
            // Load new session
            const filePath = join(this.sessionDir, sessionFile);
            const data = await readFile(filePath, 'utf8');
            const parsed = JSON.parse(data);
            
            this.state = parsed.state || parsed;
            this.sessionInfo = parsed.sessionInfo || this.sessionInfo;
            
            // Update current session file
            this.sessionFilePath = filePath;
            
            await this.saveSessionToFile();
            console.log(`🔄 Switched to session: ${sessionFile}`);
            
            return true;
            
        } catch (error) {
            console.error('❌ Failed to switch session:', error);
            return false;
        }
    }
    
    /**
     * Encryption and decryption methods
     */
    async encryptData(data) {
        if (!this.encryptionKey) return data;
        
        try {
            const iv = crypto.randomBytes(16);
            const cipher = crypto.createCipheriv('aes-256-gcm', 
                crypto.createHash('sha256').update(this.encryptionKey).digest(), 
                iv
            );
            
            let encrypted = cipher.update(data, 'utf8', 'hex');
            encrypted += cipher.final('hex');
            const authTag = cipher.getAuthTag();
            
            return JSON.stringify({
                encrypted: encrypted,
                iv: iv.toString('hex'),
                authTag: authTag.toString('hex'),
                encryptedAt: new Date().toISOString()
            });
            
        } catch (error) {
            console.error('❌ Encryption failed:', error);
            return data;
        }
    }
    
    async decryptData(encryptedData) {
        if (!this.encryptionKey) return encryptedData;
        
        try {
            const parsed = JSON.parse(encryptedData);
            if (!parsed.encrypted || !parsed.iv || !parsed.authTag) {
                return encryptedData;
            }
            
            const decipher = crypto.createDecipheriv('aes-256-gcm',
                crypto.createHash('sha256').update(this.encryptionKey).digest(),
                Buffer.from(parsed.iv, 'hex')
            );
            
            decipher.setAuthTag(Buffer.from(parsed.authTag, 'hex'));
            
            let decrypted = decipher.update(parsed.encrypted, 'hex', 'utf8');
            decrypted += decipher.final('utf8');
            
            return decrypted;
            
        } catch (error) {
            console.error('❌ Decryption failed:', error);
            return encryptedData;
        }
    }
    
    isEncryptedData(data) {
        try {
            const parsed = JSON.parse(data);
            return parsed.encrypted && parsed.iv && parsed.authTag;
        } catch (e) {
            return false;
        }
    }
    
    /**
     * Utility methods
     */
    async fileExists(filePath) {
        try {
            await stat(filePath);
            return true;
        } catch (error) {
            return false;
        }
    }
    
    async getSaveCount() {
        try {
            const countFile = join(this.sessionDir, '.save_count');
            if (await this.fileExists(countFile)) {
                const count = parseInt(await readFile(countFile, 'utf8')) || 0;
                await writeFile(countFile, (count + 1).toString());
                return count + 1;
            } else {
                await writeFile(countFile, '1');
                return 1;
            }
        } catch (error) {
            return 1;
        }
    }
    
    /**
     * Fallback auth state creation
     */
    createFallbackAuthState() {
        console.warn('⚠️ Using fallback auth state');
        const state = this.createNewAuthState();
        
        return {
            state: state,
            saveCreds: async () => {
                console.warn('⚠️ Save callback called on fallback state');
            }
        };
    }
    
    /**
     * Export session for backup
     */
    async exportSession() {
        try {
            if (!this.state) {
                throw new Error('No session to export');
            }
            
            const exportData = {
                state: this.state,
                sessionInfo: this.sessionInfo,
                exportedAt: new Date().toISOString(),
                version: '1.0.0'
            };
            
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const exportPath = join(this.sessionDir, `session_export_${timestamp}.json`);
            
            await writeFile(exportPath, JSON.stringify(exportData, null, 2), 'utf8');
            
            console.log(`📤 Session exported to: ${exportPath}`);
            return exportPath;
            
        } catch (error) {
            console.error('❌ Failed to export session:', error);
            return null;
        }
    }
}

// Helper functions (polyfill for older Node versions)
const readdir = async (path) => {
    const fs = require('fs').promises;
    return fs.readdir(path);
};

const rename = async (oldPath, newPath) => {
    const fs = require('fs').promises;
    return fs.rename(oldPath, newPath);
};

// Export the class
module.exports = AuthStateManager;

// Test the module if run directly
if (require.main === module) {
    (async () => {
        console.log('🧪 Testing Auth State Manager...\n');
        
        const authManager = new AuthStateManager('./test_session.json');
        
        // Test 1: Load or create session
        console.log('1. Loading auth state...');
        const { state, saveCreds } = await authManager.loadAuthState();
        console.log('✅ Auth state loaded\n');
        
        // Test 2: Get session info
        console.log('2. Session info:');
        console.log(authManager.getSessionInfo());
        console.log('');
        
        // Test 3: Check if valid
        console.log('3. Valid session?', await authManager.hasValidSession());
        console.log('');
        
        // Test 4: Save session
        console.log('4. Saving session...');
        await saveCreds();
        console.log('✅ Session saved\n');
        
        // Clean up test file
        const fs = require('fs').promises;
        await fs.unlink('./test_session.json').catch(() => {});
        await fs.rmdir('./data', { recursive: true }).catch(() => {});
        
        console.log('🧪 Test completed successfully');
    })().catch(console.error);
    }
