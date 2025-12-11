#!/bin/bash
# Скрипт для тестирования iikoCloud API через curl

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
USER_ID="${TEST_USER_ID:-default_user}"
API_BASE="${BACKEND_URL}/api/iiko"

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🧪 Тестирование iikoCloud API${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Backend URL: $BACKEND_URL"
echo "User ID: $USER_ID"
echo ""

# 1. Статус подключения
echo -e "${BLUE}1. Статус подключения Cloud API${NC}"
curl -s "${API_BASE}/cloud/status/${USER_ID}" | jq '.'
echo ""

# 2. Номенклатура
echo -e "${BLUE}2. Получение номенклатуры${NC}"
curl -s "${API_BASE}/cloud/menu/${USER_ID}" | jq '{organization_name, products_count, groups_count, products: .products[0:3]}'
echo ""

# 3. Отчёт по продажам (за последние 7 дней)
DATE_TO=$(date +%Y-%m-%d)
DATE_FROM=$(date -d "7 days ago" +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d 2>/dev/null || echo "2025-01-01")

echo -e "${BLUE}3. Отчёт по продажам (${DATE_FROM} - ${DATE_TO})${NC}"
curl -s "${API_BASE}/cloud/reports/sales/${USER_ID}?date_from=${DATE_FROM}&date_to=${DATE_TO}&group_by=DAY" | jq '{organization_name, date_from, date_to, report: {totalRevenue, totalChecks, averageCheck}}'
echo ""

# 4. Отчёт по остаткам
echo -e "${BLUE}4. Отчёт по остаткам${NC}"
curl -s "${API_BASE}/cloud/reports/stock/${USER_ID}?date=${DATE_TO}" | jq '.'
echo ""

# 5. Отчёт по закупкам
echo -e "${BLUE}5. Отчёт по закупкам${NC}"
curl -s "${API_BASE}/cloud/reports/purchases/${USER_ID}?date_from=${DATE_FROM}&date_to=${DATE_TO}" | jq '.'
echo ""

# 6. Заказы
echo -e "${BLUE}6. Получение заказов${NC}"
curl -s "${API_BASE}/cloud/orders/${USER_ID}?date_from=${DATE_FROM}&date_to=${DATE_TO}" | jq '{organization_name, orders: {count: .orders.count}}'
echo ""

# 7. Сотрудники
echo -e "${BLUE}7. Получение сотрудников${NC}"
curl -s "${API_BASE}/cloud/employees/${USER_ID}" | jq '{organization_name, employees: {count: .employees.count, first_3: .employees.employees[0:3]}}'
echo ""

echo -e "${GREEN}✅ Тестирование завершено${NC}"

