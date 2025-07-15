import subprocess
import sys
import os

def convert_m4a_to_pcm(input_file, output_file):
    """Convert M4A audio to PCM format using ffmpeg"""
    
    if not os.path.exists(input_file):
        print(f"❌ Input file {input_file} not found!")
        return False
    
    try:
        # Use ffmpeg to convert M4A to PCM
        # 16-bit, 16kHz, mono PCM format (common for speech processing)
        cmd = [
            'ffmpeg', 
            '-i', input_file,           # Input file
            '-f', 's16le',              # Format: 16-bit little-endian PCM
            '-ar', '16000',             # Sample rate: 16kHz
            '-ac', '1',                 # Channels: mono
            '-y',                       # Overwrite output file
            output_file
        ]
        
        print(f"🔄 Converting {input_file} to PCM format...")
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Successfully converted to {output_file}")
            
            # Check file sizes
            input_size = os.path.getsize(input_file)
            output_size = os.path.getsize(output_file)
            print(f"📊 Input size: {input_size:,} bytes")
            print(f"📊 Output size: {output_size:,} bytes")
            
            return True
        else:
            print(f"❌ Conversion failed!")
            print(f"Error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ ffmpeg not found! Please install ffmpeg first.")
        print("   Windows: Download from https://ffmpeg.org/download.html")
        print("   Or use: winget install ffmpeg")
        return False
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        return False

def check_ffmpeg():
    """Check if ffmpeg is available"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

if __name__ == "__main__":
    input_file = "TestAudio.m4a"
    output_file = "TestAudio.pcm"
    
    print("🎵 Audio Converter - M4A to PCM")
    print("=" * 40)
    
    # Check if ffmpeg is available
    if not check_ffmpeg():
        print("❌ ffmpeg is required but not found!")
        print("Please install ffmpeg first:")
        print("  Windows: winget install ffmpeg")
        print("  Or download from: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    # Convert the file
    success = convert_m4a_to_pcm(input_file, output_file)
    
    if success:
        print(f"\n🎉 Conversion complete!")
        print(f"   Original: {input_file}")
        print(f"   Converted: {output_file}")
        print(f"\nYou can now use {output_file} for voice testing.")
    else:
        print("\n❌ Conversion failed!")
        sys.exit(1) 