param(
    [string]$GeneratedImages = 'C:\Users\rafa_\.codex\generated_images\01a0d89f-a928-7721-ba5e-8326be72e92c'
)
$ErrorActionPreference = 'Stop'
$modRoot = Join-Path $PSScriptRoot 'Contents\mods\WeaponSkinShop'
$mediaRoot = Join-Path $modRoot '42.19\media'
$generatedRoot = $GeneratedImages
New-Item -ItemType Directory -Force -Path (Join-Path $modRoot 'common'), (Join-Path $mediaRoot 'textures\WSS'), (Join-Path $mediaRoot 'ui\WSS') | Out-Null

# Export AI-created source art at game asset sizes. No original textures are overwritten.
Add-Type -AssemblyName System.Drawing
function Export-Asset([string]$InputFile, [string]$OutputFile, [int]$Size) {
    $inputImage = [System.Drawing.Image]::FromFile($InputFile)
    $bitmap = [System.Drawing.Bitmap]::new($Size, $Size)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.DrawImage($inputImage, 0, 0, $Size, $Size)
        $bitmap.Save($OutputFile, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally { $graphics.Dispose(); $bitmap.Dispose(); $inputImage.Dispose() }
}
Export-Asset (Join-Path $generatedRoot 'exec-94fd0798-d81d-4ef4-9225-1f6eb51f9051.png') (Join-Path $mediaRoot 'textures\WSS\AK47_Cobalt.png') 256
Export-Asset (Join-Path $generatedRoot 'exec-fea9678c-36e3-4dcf-afe0-87575446e366.png') (Join-Path $mediaRoot 'ui\WSS\AK47_Cobalt.png') 512
Export-Asset (Join-Path $generatedRoot 'exec-cd06c3cf-54ba-48b2-983d-3aa3c5ebd6fa.png') (Join-Path $mediaRoot 'ui\WSS\AK47_Cyberpunk.png') 512
Copy-Item -LiteralPath (Join-Path $mediaRoot 'ui\WSS\AK47_Cobalt.png') -Destination (Join-Path $modRoot '42.19\poster.png')
Write-Output 'AK-47 Cobalt UV texture and Cobalt/Cyberpunk 512px shop previews exported.'
