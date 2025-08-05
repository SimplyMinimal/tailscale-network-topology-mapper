package utils

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// FileExists checks if a file exists
func FileExists(filename string) bool {
	_, err := os.Stat(filename)
	return !os.IsNotExist(err)
}

// EnsureDir ensures that a directory exists, creating it if necessary
func EnsureDir(dir string) error {
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		return os.MkdirAll(dir, 0755)
	}
	return nil
}

// GetFileExtension returns the file extension (without the dot)
func GetFileExtension(filename string) string {
	ext := filepath.Ext(filename)
	if len(ext) > 0 {
		return ext[1:] // Remove the dot
	}
	return ""
}

// IsValidPolicyFile checks if a file has a valid policy file extension
func IsValidPolicyFile(filename string) bool {
	ext := strings.ToLower(GetFileExtension(filename))
	validExtensions := []string{"json", "hujson", "hjson"}
	
	for _, validExt := range validExtensions {
		if ext == validExt {
			return true
		}
	}
	return false
}

// FindPolicyFile searches for a policy file in common locations
func FindPolicyFile() (string, error) {
	// Common policy file names
	candidates := []string{
		"policy.hujson",
		"policy.hjson",
		"policy.json",
		"acl.hujson",
		"acl.hjson",
		"acl.json",
		"tailscale-policy.hujson",
		"tailscale-policy.hjson",
		"tailscale-policy.json",
	}

	// Search in current directory first
	for _, candidate := range candidates {
		if FileExists(candidate) {
			return candidate, nil
		}
	}

	// Search in common subdirectories
	searchDirs := []string{
		"config",
		"configs",
		"policy",
		"policies",
		"acl",
		"acls",
	}

	for _, dir := range searchDirs {
		if _, err := os.Stat(dir); err == nil {
			for _, candidate := range candidates {
				path := filepath.Join(dir, candidate)
				if FileExists(path) {
					return path, nil
				}
			}
		}
	}

	return "", fmt.Errorf("no policy file found in current directory or common subdirectories")
}

// GetAbsolutePath returns the absolute path of a file
func GetAbsolutePath(filename string) (string, error) {
	return filepath.Abs(filename)
}

// GetRelativePath returns the relative path from base to target
func GetRelativePath(base, target string) (string, error) {
	return filepath.Rel(base, target)
}

// SanitizeFilename removes or replaces invalid characters in a filename
func SanitizeFilename(filename string) string {
	// Replace invalid characters with underscores
	invalid := []string{"/", "\\", ":", "*", "?", "\"", "<", ">", "|"}
	sanitized := filename
	
	for _, char := range invalid {
		sanitized = strings.ReplaceAll(sanitized, char, "_")
	}
	
	// Remove leading/trailing spaces and dots
	sanitized = strings.Trim(sanitized, " .")
	
	// Ensure filename is not empty
	if sanitized == "" {
		sanitized = "unnamed"
	}
	
	return sanitized
}

// GetUniqueFilename generates a unique filename by appending a number if needed
func GetUniqueFilename(filename string) string {
	if !FileExists(filename) {
		return filename
	}

	ext := filepath.Ext(filename)
	base := strings.TrimSuffix(filename, ext)
	
	for i := 1; i < 1000; i++ {
		candidate := fmt.Sprintf("%s_%d%s", base, i, ext)
		if !FileExists(candidate) {
			return candidate
		}
	}
	
	// If we can't find a unique name, append timestamp
	timestamp := fmt.Sprintf("%d", os.Getpid())
	return fmt.Sprintf("%s_%s%s", base, timestamp, ext)
}

// CopyFile copies a file from src to dst
func CopyFile(src, dst string) error {
	sourceFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer sourceFile.Close()

	destFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer destFile.Close()

	_, err = destFile.ReadFrom(sourceFile)
	return err
}

// BackupFile creates a backup of a file with a .bak extension
func BackupFile(filename string) error {
	if !FileExists(filename) {
		return fmt.Errorf("file does not exist: %s", filename)
	}

	backupName := filename + ".bak"
	backupName = GetUniqueFilename(backupName)
	
	return CopyFile(filename, backupName)
}

// GetFileSize returns the size of a file in bytes
func GetFileSize(filename string) (int64, error) {
	info, err := os.Stat(filename)
	if err != nil {
		return 0, err
	}
	return info.Size(), nil
}

// IsDirectory checks if a path is a directory
func IsDirectory(path string) bool {
	info, err := os.Stat(path)
	if err != nil {
		return false
	}
	return info.IsDir()
}

// ListFiles returns a list of files in a directory with optional extension filter
func ListFiles(dir string, extensions ...string) ([]string, error) {
	var files []string
	
	err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		
		if info.IsDir() {
			return nil
		}
		
		// If no extensions specified, include all files
		if len(extensions) == 0 {
			files = append(files, path)
			return nil
		}
		
		// Check if file has one of the specified extensions
		fileExt := strings.ToLower(GetFileExtension(path))
		for _, ext := range extensions {
			if strings.ToLower(ext) == fileExt {
				files = append(files, path)
				break
			}
		}
		
		return nil
	})
	
	return files, err
}

// CreateTempFile creates a temporary file with the specified prefix and suffix
func CreateTempFile(prefix, suffix string) (*os.File, error) {
	return os.CreateTemp("", prefix+"*"+suffix)
}

// WriteStringToFile writes a string to a file
func WriteStringToFile(filename, content string) error {
	return os.WriteFile(filename, []byte(content), 0644)
}

// ReadStringFromFile reads a file and returns its content as a string
func ReadStringFromFile(filename string) (string, error) {
	content, err := os.ReadFile(filename)
	if err != nil {
		return "", err
	}
	return string(content), nil
}
