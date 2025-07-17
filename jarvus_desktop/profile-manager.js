const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { spawn } = require('child_process');

class SecureProfileManager {
    constructor(appInstancePath = null) {
        this.baseDir = appInstancePath 
            ? path.join(appInstancePath, 'secure_profiles')
            : path.join(os.tmpdir(), 'jarvus_secure_profiles');
        
        // Ensure base directory exists
        if (!fs.existsSync(this.baseDir)) {
            fs.mkdirSync(this.baseDir, { recursive: true });
        }
        
        this.encryptionKey = this.getOrCreateEncryptionKey();
        // Remove hardcoded profile - will be determined dynamically
        
        console.log(`Secure Profile Manager initialized at: ${this.baseDir}`);
        console.log('Using dynamic profile selection');
    }
    
    getOrCreateEncryptionKey() {
        const keyFile = path.join(this.baseDir, '.encryption_key');
        
        if (fs.existsSync(keyFile)) {
            try {
                return fs.readFileSync(keyFile);
            } catch (error) {
                console.warn(`Failed to read existing encryption key: ${error.message}`);
            }
        }
        
        // Generate new key
        const key = crypto.randomBytes(32);
        try {
            fs.writeFileSync(keyFile, key);
            console.log('Generated new encryption key for profile encryption');
        } catch (error) {
            console.error(`Failed to save encryption key: ${error.message}`);
        }
        
        return key;
    }
    
    getChromeUserDataPath() {
        const home = os.homedir();
        
        if (process.platform === 'win32') {
            return path.join(home, 'AppData', 'Local', 'Google', 'Chrome');
        } else if (process.platform === 'darwin') {
            return path.join(home, 'Library', 'Application Support', 'Google', 'Chrome');
        } else {
            return path.join(home, '.config', 'google-chrome');
        }
    }
    
    getChromeProfilePath(profileName = null) {
        if (!profileName) {
            console.warn('No profile name provided to getChromeProfilePath');
            return null;
        }
        
        const userDataPath = this.getChromeUserDataPath();
        const profilePath = path.join(userDataPath, profileName);
        
        if (fs.existsSync(profilePath)) {
            return profilePath;
        }
        
        return null;
    }
    
    discoverAvailableProfiles() {
        const profiles = {};
        const userDataPath = this.getChromeUserDataPath();
        
        if (!fs.existsSync(userDataPath)) {
            console.warn(`Chrome User Data directory not found: ${userDataPath}`);
            return profiles;
        }
        
        try {
            const items = fs.readdirSync(userDataPath);
            
            for (const item of items) {
                const itemPath = path.join(userDataPath, item);
                const stats = fs.statSync(itemPath);
                
                if (stats.isDirectory()) {
                    const profileName = item;
                    
                    // Skip system directories
                    if (['System Profile', 'Guest Profile'].includes(profileName)) {
                        continue;
                    }
                    
                    // Check if it's a valid profile directory
                    const preferencesFile = path.join(itemPath, 'Preferences');
                    if (fs.existsSync(preferencesFile)) {
                        const profileInfo = this.extractProfileInfo(itemPath, profileName);
                        if (profileInfo) {
                            profiles[profileName] = profileInfo;
                        }
                    }
                }
            }
            
            console.log(`Discovered ${Object.keys(profiles).length} Chrome profiles: ${Object.keys(profiles)}`);
            return profiles;
            
        } catch (error) {
            console.error(`Error discovering Chrome profiles: ${error.message}`);
            return profiles;
        }
    }
    
    extractProfileInfo(profilePath, profileName) {
        try {
            const preferencesFile = path.join(profilePath, 'Preferences');
            if (!fs.existsSync(preferencesFile)) {
                return null;
            }
            
            const prefsData = JSON.parse(fs.readFileSync(preferencesFile, 'utf8'));
            
            const profileInfo = {
                name: profileName,
                path: profilePath,
                display_name: profileName,
                email: null,
                full_name: null,
                avatar_icon: null,
                is_ephemeral: false,
                is_consented_primary_account: false
            };
            
            // Extract profile information from Preferences
            if (prefsData.profile) {
                const profileData = prefsData.profile;
                if (profileData.name) {
                    profileInfo.display_name = profileData.name;
                }
                
                // Extract account information if available
                if (profileData.gaia_name) {
                    profileInfo.full_name = profileData.gaia_name;
                }
                if (profileData.user_name) {
                    profileInfo.email = profileData.user_name;
                }
                if (profileData.avatar_icon) {
                    profileInfo.avatar_icon = profileData.avatar_icon;
                }
                if (profileData.is_ephemeral !== undefined) {
                    profileInfo.is_ephemeral = profileData.is_ephemeral;
                }
                if (profileData.is_consented_primary_account !== undefined) {
                    profileInfo.is_consented_primary_account = profileData.is_consented_primary_account;
                }
            }
            
            // Also check for account information in other sections
            if (prefsData.account_id_migration) {
                const accountData = prefsData.account_id_migration;
                if (accountData.email && !profileInfo.email) {
                    profileInfo.email = accountData.email;
                }
            }
            
            // Check for signin information
            if (prefsData.signin) {
                const signinData = prefsData.signin;
                if (signinData.last_used) {
                    profileInfo.last_signin = signinData.last_used;
                }
            }
            
            // Check for sync information
            if (prefsData.sync) {
                const syncData = prefsData.sync;
                if (syncData.requested !== undefined) {
                    profileInfo.sync_enabled = syncData.requested;
                }
            }
            
            return profileInfo;
            
        } catch (error) {
            console.error(`Error extracting profile info from ${profilePath}: ${error.message}`);
            return null;
        }
    }
    
    getDefaultProfile() {
        const profiles = this.discoverAvailableProfiles();
        
        // Look for the primary account profile
        for (const [profileName, profileInfo] of Object.entries(profiles)) {
            if (profileInfo.is_consented_primary_account) {
                console.log(`Found primary account profile: ${profileName}`);
                return profileName;
            }
        }
        
        // If no primary account found, return the first available profile
        const profileNames = Object.keys(profiles);
        if (profileNames.length > 0) {
            console.log(`Using first available profile: ${profileNames[0]}`);
            return profileNames[0];
        }
        
        console.warn('No profiles found');
        return null;
    }
    
    getEssentialProfileFiles() {
        return [
            "Preferences",
            "Cookies",
            "Login Data",
            "Web Data",
            "History",
            "Bookmarks",
            "Favicons",
            "Shortcuts",
            "Top Sites",
            "Visited Links",
            "Last Session",
            "Last Tabs",
            "Current Session",
            "Current Tabs",
            "Sessions",
            "Extension State",
            "Extension Rules",
            "Local State",
            "Network Action Predictor",
            "Network Persistent State",
            "Origin Bound Certs",
            "QuotaManager",
            "QuotaManager-journal",
            "TransportSecurity",
            "Trust Tokens",
            "WebRTCIdentityStore",
            "WebRTCIdentityStore-journal"
        ];
    }
    
    getEssentialDirectories() {
        return [
            "Extensions",
            "Local Extension Settings",
            "Sync Extension Settings",
            "Storage",
            "IndexedDB",
            "Local Storage",
            "Session Storage",
            "WebStorage",
            "GPUCache",
            "Code Cache",
            "Service Worker",
            "File System",
            "File System Access",
            "BackgroundFetch",
            "Background Sync",
            "Push Messaging",
            "Payment Handler",
            "Web App Shortcuts",
            "Web App Icons",
            "Web App Manifest",
            "Web App Data",
            "Web App Installations",
            "Web App Installations-journal",
            "Web App Installations-000",
            "Web App Installations-001",
            "Web App Installations-002",
            "Web App Installations-003",
            "Web App Installations-004",
            "Web App Installations-005",
            "Web App Installations-006",
            "Web App Installations-007",
            "Web App Installations-008",
            "Web App Installations-009",
            "Web App Installations-00a",
            "Web App Installations-00b",
            "Web App Installations-00c",
            "Web App Installations-00d",
            "Web App Installations-00e",
            "Web App Installations-00f"
        ];
    }
    
    encryptFile(sourcePath, destPath) {
        try {
            if (!fs.existsSync(sourcePath)) {
                return false;
            }
            
            // Read source file
            const data = fs.readFileSync(sourcePath);
            
            // Create cipher
            const algorithm = 'aes-256-cbc';
            const iv = crypto.randomBytes(16);
            const cipher = crypto.createCipher(algorithm, this.encryptionKey);
            
            // Encrypt data
            let encrypted = cipher.update(data, 'utf8', 'hex');
            encrypted += cipher.final('hex');
            
            // Write encrypted file with IV
            const encryptedData = iv.toString('hex') + ':' + encrypted;
            fs.writeFileSync(destPath, encryptedData);
            
            return true;
        } catch (error) {
            console.error(`Failed to encrypt file ${sourcePath}: ${error.message}`);
            return false;
        }
    }
    
    decryptFile(sourcePath, destPath) {
        try {
            if (!fs.existsSync(sourcePath)) {
                return false;
            }
            
            // Read encrypted file
            const encryptedData = fs.readFileSync(sourcePath, 'utf8');
            
            // Split IV and encrypted data
            const parts = encryptedData.split(':');
            const iv = Buffer.from(parts[0], 'hex');
            const encrypted = parts[1];
            
            // Create decipher
            const algorithm = 'aes-256-cbc';
            const decipher = crypto.createDecipher(algorithm, this.encryptionKey);
            decipher.setAutoPadding(false);
            
            // Decrypt data
            let decrypted = decipher.update(encrypted, 'hex', 'utf8');
            decrypted += decipher.final('utf8');
            
            // Write decrypted file
            fs.writeFileSync(destPath, decrypted);
            
            return true;
        } catch (error) {
            console.error(`Failed to decrypt file ${sourcePath}: ${error.message}`);
            return false;
        }
    }
    
    copyDirectoryEncrypted(sourceDir, destDir) {
        let copiedCount = 0;
        
        try {
            if (!fs.existsSync(sourceDir)) {
                return copiedCount;
            }
            
            if (!fs.existsSync(destDir)) {
                fs.mkdirSync(destDir, { recursive: true });
            }
            
            const items = fs.readdirSync(sourceDir);
            
            for (const item of items) {
                const sourcePath = path.join(sourceDir, item);
                const stats = fs.statSync(sourcePath);
                
                if (stats.isFile()) {
                    const encryptedPath = path.join(destDir, `${item}.encrypted`);
                    if (this.encryptFile(sourcePath, encryptedPath)) {
                        copiedCount++;
                    }
                } else if (stats.isDirectory()) {
                    const subDest = path.join(destDir, item);
                    copiedCount += this.copyDirectoryEncrypted(sourcePath, subDest);
                }
            }
            
            return copiedCount;
        } catch (error) {
            console.error(`Failed to copy directory ${sourceDir}: ${error.message}`);
            return copiedCount;
        }
    }
    
    copyDirectoryDecrypted(sourceDir, destDir) {
        let copiedCount = 0;
        
        try {
            if (!fs.existsSync(sourceDir)) {
                return copiedCount;
            }
            
            if (!fs.existsSync(destDir)) {
                fs.mkdirSync(destDir, { recursive: true });
            }
            
            const items = fs.readdirSync(sourceDir);
            
            for (const item of items) {
                const sourcePath = path.join(sourceDir, item);
                const stats = fs.statSync(sourcePath);
                
                if (stats.isFile() && item.endsWith('.encrypted')) {
                    // Remove .encrypted extension
                    const originalName = item.slice(0, -10); // Remove '.encrypted'
                    const decryptedPath = path.join(destDir, originalName);
                    if (this.decryptFile(sourcePath, decryptedPath)) {
                        copiedCount++;
                    }
                } else if (stats.isDirectory()) {
                    const subDest = path.join(destDir, item);
                    copiedCount += this.copyDirectoryDecrypted(sourcePath, subDest);
                }
            }
            
            return copiedCount;
        } catch (error) {
            console.error(`Failed to copy directory ${sourceDir}: ${error.message}`);
            return copiedCount;
        }
    }
    
    createSecureProfileCopy(profileName = null) {
        try {
            // Get source profile path
            const sourceProfile = this.getChromeProfilePath(profileName);
            if (!sourceProfile) {
                console.warn(`Could not find Chrome profile: ${profileName}`);
                return null;
            }
            
            if (!fs.existsSync(sourceProfile)) {
                console.warn(`Chrome profile not found at: ${sourceProfile}`);
                console.log('Creating empty secure profile for Playwright');
                
                // Create an empty secure profile directory for Playwright to use
                const profileHash = crypto.createHash('sha256').update(`empty_${profileName}`).digest('hex').slice(0, 16);
                const secureProfileDir = path.join(this.baseDir, `${profileName}_${profileHash}`);
                
                if (!fs.existsSync(secureProfileDir)) {
                    fs.mkdirSync(secureProfileDir, { recursive: true });
                }
                
                // Save metadata for empty profile
                const metadata = {
                    source_profile: 'empty_profile',
                    created_at: new Date().toISOString(),
                    copied_files: 0,
                    profile_name: profileName,
                    profile_hash: profileHash,
                    is_empty: true
                };
                
                const metadataFile = path.join(secureProfileDir, 'metadata.json');
                fs.writeFileSync(metadataFile, JSON.stringify(metadata, null, 2));
                
                console.log(`Created empty secure profile at: ${secureProfileDir}`);
                return secureProfileDir;
            }
            
            // Create destination directory
            const profileHash = crypto.createHash('sha256').update(sourceProfile).digest('hex').slice(0, 16);
            const secureProfileDir = path.join(this.baseDir, `${profileName}_${profileHash}`);
            
            if (!fs.existsSync(secureProfileDir)) {
                fs.mkdirSync(secureProfileDir, { recursive: true });
            }
            
            console.log(`Creating secure profile copy from: ${sourceProfile}`);
            console.log(`Secure profile location: ${secureProfileDir}`);
            
            let copiedFiles = 0;
            
            // Copy essential files
            for (const filename of this.getEssentialProfileFiles()) {
                const sourceFile = path.join(sourceProfile, filename);
                if (fs.existsSync(sourceFile) && fs.statSync(sourceFile).isFile()) {
                    const encryptedFile = path.join(secureProfileDir, `${filename}.encrypted`);
                    if (this.encryptFile(sourceFile, encryptedFile)) {
                        copiedFiles++;
                    }
                }
            }
            
            // Copy essential directories
            for (const dirname of this.getEssentialDirectories()) {
                const sourceDir = path.join(sourceProfile, dirname);
                if (fs.existsSync(sourceDir) && fs.statSync(sourceDir).isDirectory()) {
                    const destDir = path.join(secureProfileDir, dirname);
                    copiedFiles += this.copyDirectoryEncrypted(sourceDir, destDir);
                }
            }
            
            // Save metadata
            const metadata = {
                source_profile: sourceProfile,
                created_at: new Date().toISOString(),
                copied_files: copiedFiles,
                profile_name: profileName,
                profile_hash: profileHash
            };
            
            const metadataFile = path.join(secureProfileDir, 'metadata.json');
            fs.writeFileSync(metadataFile, JSON.stringify(metadata, null, 2));
            
            console.log(`Secure profile copy created with ${copiedFiles} files/directories`);
            return secureProfileDir;
            
        } catch (error) {
            console.error(`Failed to create secure profile copy: ${error.message}`);
            return null;
        }
    }
    
    getPlaywrightProfilePath(profileName = null) {
        try {
            // Find the secure profile directory
            const profileDirs = fs.readdirSync(this.baseDir)
                .filter(item => {
                    const itemPath = path.join(this.baseDir, item);
                    return fs.statSync(itemPath).isDirectory() && item.startsWith(`${profileName}_`);
                })
                .map(item => path.join(this.baseDir, item));
            
            if (profileDirs.length === 0) {
                console.warn(`No secure profile found for: ${profileName}`);
                return null;
            }
            
            // Use the most recent one
            const secureProfileDir = profileDirs.reduce((latest, current) => {
                const latestStats = fs.statSync(latest);
                const currentStats = fs.statSync(current);
                return currentStats.mtime > latestStats.mtime ? current : latest;
            });
            
            // Create decrypted profile directory
            const decryptedProfileDir = path.join(this.baseDir, `playwright_${profileName}_decrypted`);
            
            if (!fs.existsSync(decryptedProfileDir)) {
                fs.mkdirSync(decryptedProfileDir, { recursive: true });
            }
            
            console.log(`Decrypting profile from: ${secureProfileDir}`);
            console.log(`Decrypted profile location: ${decryptedProfileDir}`);
            
            let copiedFiles = 0;
            
            // Decrypt files
            const items = fs.readdirSync(secureProfileDir);
            
            for (const item of items) {
                const itemPath = path.join(secureProfileDir, item);
                const stats = fs.statSync(itemPath);
                
                if (stats.isFile() && item.endsWith('.encrypted')) {
                    // Remove .encrypted extension
                    const originalName = item.slice(0, -10);
                    const decryptedFile = path.join(decryptedProfileDir, originalName);
                    if (this.decryptFile(itemPath, decryptedFile)) {
                        copiedFiles++;
                    }
                } else if (stats.isDirectory()) {
                    const subDest = path.join(decryptedProfileDir, item);
                    copiedFiles += this.copyDirectoryDecrypted(itemPath, subDest);
                }
            }
            
            console.log(`Decrypted ${copiedFiles} files/directories for Playwright`);
            return decryptedProfileDir;
            
        } catch (error) {
            console.error(`Failed to get Playwright profile path: ${error.message}`);
            return null;
        }
    }
    
    syncProfileData(profileName = null) {
        try {
            console.log(`Syncing profile data for: ${profileName}`);
            
            // Create a fresh secure copy
            const secureProfileDir = this.createSecureProfileCopy(profileName);
            if (!secureProfileDir) {
                return false;
            }
            
            // Get the Playwright profile path (this will decrypt the new copy)
            const playwrightProfile = this.getPlaywrightProfilePath(profileName);
            if (!playwrightProfile) {
                return false;
            }
            
            console.log('Profile sync completed successfully');
            return true;
            
        } catch (error) {
            console.error(`Failed to sync profile data: ${error.message}`);
            return false;
        }
    }
    
    getProfileInfo(profileName = null) {
        try {
            const profileDirs = fs.readdirSync(this.baseDir)
                .filter(item => {
                    const itemPath = path.join(this.baseDir, item);
                    return fs.statSync(itemPath).isDirectory() && item.startsWith(`${profileName}_`);
                })
                .map(item => path.join(this.baseDir, item));
            
            if (profileDirs.length === 0) {
                return null;
            }
            
            const secureProfileDir = profileDirs.reduce((latest, current) => {
                const latestStats = fs.statSync(latest);
                const currentStats = fs.statSync(current);
                return currentStats.mtime > latestStats.mtime ? current : latest;
            });
            
            const metadataFile = path.join(secureProfileDir, 'metadata.json');
            
            if (fs.existsSync(metadataFile)) {
                const metadata = JSON.parse(fs.readFileSync(metadataFile, 'utf8'));
                
                // Add current status
                metadata.secure_profile_path = secureProfileDir;
                metadata.playwright_profile_path = this.getPlaywrightProfilePath(profileName);
                metadata.last_modified = new Date(fs.statSync(secureProfileDir).mtime).toISOString();
                
                return metadata;
            }
            
            return null;
            
        } catch (error) {
            console.error(`Failed to get profile info: ${error.message}`);
            return null;
        }
    }
    
    // Method to get the decrypted profile path for Python to use
    getDecryptedProfilePath(profileName = null) {
        return this.getPlaywrightProfilePath(profileName);
    }

    // Check if a profile is available (not locked by another Chrome instance)
    isProfileAvailable(profileName) {
        const profilePath = this.getChromeProfilePath(profileName);
        if (!profilePath) return false;
        
        // Check for lock files
        const lockFile = path.join(profilePath, 'lockfile');
        const singletonLock = path.join(profilePath, 'SingletonLock');
        
        return !fs.existsSync(lockFile) && !fs.existsSync(singletonLock);
    }

    // Get all available profiles (not locked by other Chrome instances)
    getAvailableProfiles() {
        const allProfiles = this.discoverAvailableProfiles();
        const availableProfiles = {};
        
        for (const [name, info] of Object.entries(allProfiles)) {
            if (this.isProfileAvailable(name)) {
                availableProfiles[name] = info;
            }
        }
        
        console.log(`Found ${Object.keys(availableProfiles).length} available profiles: ${Object.keys(availableProfiles)}`);
        return availableProfiles;
    }

    // Get the best available profile (primary account first, then first available)
    getBestAvailableProfile() {
        const availableProfiles = this.getAvailableProfiles();
        
        if (Object.keys(availableProfiles).length === 0) {
            console.warn('No available profiles found');
            return null;
        }
        
        // First, try to find the primary account profile
        for (const [name, info] of Object.entries(availableProfiles)) {
            if (info.is_consented_primary_account) {
                console.log(`Using primary account profile: ${name}`);
                return name;
            }
        }
        
        // If no primary account found, use the first available profile
        const firstProfile = Object.keys(availableProfiles)[0];
        console.log(`Using first available profile: ${firstProfile}`);
        return firstProfile;
    }
}

module.exports = SecureProfileManager; 