#!/bin/bash

# Script to create all SCRUM story pull requests
# Run this after authenticating with: gh auth login

echo "Creating pull requests for all SCRUM stories..."

# SCRUM-13: DHL, FedEx, UPS Carrier Integrations
echo "Creating PR for SCRUM-13..."
gh pr create \
  --base main \
  --head feature/SCRUM-13-shipping-carriers-integration \
  --title "feat: SCRUM-13 - DHL, FedEx, UPS Carrier Integrations" \
  --body-file PR_SCRUM_13_description.md \
  --label enhancement,feature,backend,api,high

# SCRUM-14: Exchange Rate API Integration
echo "Creating PR for SCRUM-14..."
gh pr create \
  --base main \
  --head feature/SCRUM-14-exchange-rate-integration \
  --title "feat: SCRUM-14 - Exchange Rate API Integration with Banco de la República" \
  --body-file PR_SCRUM_14_description.md \
  --label enhancement,feature,backend,api,high

# SCRUM-39: Multi-Carrier Quotation System
echo "Creating PR for SCRUM-39..."
gh pr create \
  --base main \
  --head feature/SCRUM-39-multi-carrier-quotations \
  --title "feat: SCRUM-39 - Multi-Carrier Quotation and Comparison System" \
  --body-file PR_SCRUM_39_description.md \
  --label enhancement,feature,backend,api,high

# SCRUM-46: Bulk Shipment Loading System
echo "Creating PR for SCRUM-46..."
gh pr create \
  --base main \
  --head feature/SCRUM-46-bulk-shipment-loading \
  --title "feat: SCRUM-46 - Bulk Shipment Loading System" \
  --body-file PR_SCRUM_46_description.md \
  --label enhancement,feature,backend,api,medium

# SCRUM-48: Bulk Tracking Dashboard System
echo "Creating PR for SCRUM-48..."
gh pr create \
  --base main \
  --head feature/SCRUM-48-bulk-tracking-dashboard \
  --title "feat: SCRUM-48 - Bulk Tracking Dashboard System" \
  --body-file PR_SCRUM_48_description.md \
  --label enhancement,feature,backend,api,medium

echo "All pull requests created successfully!"
echo "You can view them at: https://github.com/oscar-alvarez-quenty/Quenty/pulls"