#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p artifacts
case "${1:-}" in
  simulator)
    xcodebuild -project ios/Poochcam.xcodeproj -scheme Poochcam -configuration Debug \
      -destination 'generic/platform=iOS Simulator' -derivedDataPath artifacts/simulator \
      -clonedSourcePackagesDirPath artifacts/SourcePackages -onlyUsePackageVersionsFromResolvedFile \
      CODE_SIGNING_ALLOWED=NO ARCHS=arm64 ONLY_ACTIVE_ARCH=YES build
    ;;
  release)
    xcodebuild -project ios/Poochcam.xcodeproj -scheme Poochcam -configuration Release \
      -destination 'generic/platform=iOS' -derivedDataPath artifacts/release \
      -clonedSourcePackagesDirPath artifacts/SourcePackages -onlyUsePackageVersionsFromResolvedFile \
      CODE_SIGNING_ALLOWED=NO build
    ;;
  *) echo 'Usage: tools/build_ios.sh simulator|release' >&2; exit 2 ;;
esac
