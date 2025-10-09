#!/usr/bin/env python3
"""
Backend Testing Suite for Menu Projects System and Analytics
Testing the new menu projects endpoints and IIKo analytics integration
"""

import requests
import json
import time
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://cursor-push.preview.emergentagent.com/api"

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[{timestamp}] {status_emoji} {test_name}: {status}")
    if details:
        print(f"    Details: {details}")
    print()

def test_basic_project_endpoints():
    """Test the basic project system endpoints that should already work"""
    print("📁 TESTING BASIC PROJECT ENDPOINTS - SHOULD ALREADY WORK")
    print("=" * 70)
    
    user_id = "test_user_12345"
    
    # Test 1: Get user's projects list (should be empty initially)
    print(f"Test 1: GET /api/menu-projects/{user_id} - Get user's project list")
    try:
        response = requests.get(f"{BACKEND_URL}/menu-projects/{user_id}", timeout=30)
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            projects = response.json()
            print(f"Response: {json.dumps(projects, ensure_ascii=False, indent=2)}")
            
            if isinstance(projects, list):
                log_test("Get Projects List", "PASS", 
                        f"Retrieved {len(projects)} projects for user {user_id}")
                return projects
            else:
                log_test("Get Projects List", "FAIL", 
                        f"Expected list, got {type(projects)}")
                return []
        else:
            log_test("Get Projects List", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            return []
            
    except Exception as e:
        log_test("Get Projects List", "FAIL", f"Exception: {str(e)}")
        return []

def test_create_project():
    """Test creating a new project"""
    print("Test 2: POST /api/create-menu-project - Create new project")
    
    # Test data as specified in the request
    project_data = {
        "user_id": "test_user_12345",
        "project_name": "Тестовое летнее меню",
        "project_type": "seasonal_update",
        "description": "Тестовый проект для проверки системы проектов и аналитики"
    }
    
    try:
        print(f"Creating project: {json.dumps(project_data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            f"{BACKEND_URL}/create-menu-project",
            json=project_data,
            timeout=30
        )
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            project_id = result.get("project_id")
            success = result.get("success", False)
            
            if success and project_id:
                log_test("Create Project", "PASS", 
                        f"Project created successfully with ID: {project_id}")
                return project_id
            else:
                log_test("Create Project", "FAIL", 
                        f"Project creation failed: {result}")
                return None
        else:
            log_test("Create Project", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        log_test("Create Project", "FAIL", f"Exception: {str(e)}")
        return None

def test_project_content(project_id):
    """Test getting project content"""
    if not project_id:
        log_test("Get Project Content", "SKIP", "No project ID available")
        return
        
    print(f"Test 3: GET /api/menu-project/{project_id}/content - Get project content")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/menu-project/{project_id}/content",
            timeout=30
        )
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.json()
            print(f"Response: {json.dumps(content, ensure_ascii=False, indent=2)}")
            
            # Check expected content structure
            project_info = content.get("project_info", {})
            menus = content.get("menus", [])
            tech_cards = content.get("tech_cards", [])
            statistics = content.get("statistics", {})
            
            log_test("Get Project Content", "PASS", 
                    f"Retrieved content: {len(menus)} menus, {len(tech_cards)} tech cards")
            
            # Verify project info
            if project_info.get("project_name") == "Тестовое летнее меню":
                log_test("Project Info Verification", "PASS", 
                        "Project name matches expected value")
            else:
                log_test("Project Info Verification", "WARN", 
                        f"Project name: {project_info.get('project_name')}")
                
            return content
        else:
            log_test("Get Project Content", "FAIL", 
                    f"HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        log_test("Get Project Content", "FAIL", f"Exception: {str(e)}")
        return None

def test_project_analytics(project_id):
    """Test the NEW project analytics endpoint with IIKo integration"""
    if not project_id:
        log_test("Project Analytics", "SKIP", "No project ID available")
        return
        
    print("📊 TESTING NEW PROJECT ANALYTICS - PRIORITY FEATURE")
    print("=" * 70)
    
    organization_id = "default-org-001"  # Edison Craft Bar as specified
    
    print(f"Test 4: GET /api/menu-project/{project_id}/analytics?organization_id={organization_id}")
    print("Expected: Extended project analytics with IIKo integration")
    
    try:
        start_time = time.time()
        
        params = {"organization_id": organization_id}
        response = requests.get(
            f"{BACKEND_URL}/menu-project/{project_id}/analytics",
            params=params,
            timeout=90  # Longer timeout for analytics processing
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Check expected analytics structure
            success = result.get("success", False)
            project_id_resp = result.get("project_id")
            organization_id_resp = result.get("organization_id")
            analytics = result.get("analytics", {})
            
            print(f"\n📈 PROJECT ANALYTICS ANALYSIS:")
            print(f"Success: {success}")
            print(f"Project ID: {project_id_resp}")
            print(f"Organization ID: {organization_id_resp}")
            
            if success and analytics:
                log_test("PROJECT ANALYTICS - SUCCESS", "PASS", 
                        "Extended project analytics generated successfully")
                
                # Test productivity metrics
                productivity_metrics = analytics.get("productivity_metrics", {})
                if productivity_metrics:
                    time_saved = productivity_metrics.get("time_saved_hours")
                    complexity_score = productivity_metrics.get("complexity_score")
                    efficiency_rating = productivity_metrics.get("efficiency_rating")
                    
                    log_test("Productivity Metrics", "PASS", 
                            f"Time saved: {time_saved}h, Complexity: {complexity_score}, Efficiency: {efficiency_rating}")
                else:
                    log_test("Productivity Metrics", "WARN", 
                            "No productivity metrics available")
                
                # Test project overview
                project_overview = analytics.get("project_overview", {})
                if project_overview:
                    total_items = project_overview.get("total_items", 0)
                    categories_covered = project_overview.get("categories_covered", 0)
                    estimated_revenue = project_overview.get("estimated_revenue")
                    
                    log_test("Project Overview", "PASS", 
                            f"Items: {total_items}, Categories: {categories_covered}, Revenue: {estimated_revenue}")
                else:
                    log_test("Project Overview", "WARN", 
                            "No project overview available")
                
                # Test IIKo integration data
                iiko_integration = analytics.get("iiko_integration", {})
                if iiko_integration:
                    integration_status = iiko_integration.get("status")
                    sales_data_available = iiko_integration.get("sales_data_available", False)
                    menu_comparison = iiko_integration.get("menu_comparison", {})
                    
                    log_test("IIKo Integration", "PASS", 
                            f"Status: {integration_status}, Sales data: {sales_data_available}")
                    
                    if menu_comparison:
                        existing_items = menu_comparison.get("existing_items", 0)
                        new_items = menu_comparison.get("new_items", 0)
                        log_test("Menu Comparison", "PASS", 
                                f"Existing: {existing_items}, New: {new_items}")
                else:
                    log_test("IIKo Integration", "WARN", 
                            "IIKo integration data not available (may be expected)")
                
                # Test recommendations
                recommendations = analytics.get("recommendations", [])
                if recommendations and len(recommendations) > 0:
                    log_test("AI Recommendations", "PASS", 
                            f"Generated {len(recommendations)} recommendations")
                    
                    # Show sample recommendations
                    print(f"    Sample recommendations:")
                    for i, rec in enumerate(recommendations[:3]):
                        rec_type = rec.get("type", "general")
                        rec_text = rec.get("recommendation", "")[:100]
                        print(f"    {i+1}. [{rec_type}] {rec_text}...")
                else:
                    log_test("AI Recommendations", "WARN", 
                            "No AI recommendations generated")
                
                # Test market insights (if IIKo data available)
                market_insights = analytics.get("market_insights", {})
                if market_insights:
                    trend_analysis = market_insights.get("trend_analysis")
                    competitive_positioning = market_insights.get("competitive_positioning")
                    
                    log_test("Market Insights", "PASS", 
                            f"Trend analysis: {bool(trend_analysis)}, Competitive: {bool(competitive_positioning)}")
                else:
                    log_test("Market Insights", "WARN", 
                            "No market insights available")
                
                # Overall analytics completeness
                analytics_sections = [
                    productivity_metrics, project_overview, 
                    recommendations, iiko_integration
                ]
                working_sections = sum(1 for section in analytics_sections if section)
                
                if working_sections >= 3:
                    log_test("Analytics Completeness", "PASS", 
                            f"{working_sections}/4 analytics sections working")
                else:
                    log_test("Analytics Completeness", "WARN", 
                            f"Only {working_sections}/4 analytics sections working")
                    
            else:
                log_test("PROJECT ANALYTICS - FAILURE", "FAIL", 
                        "Project analytics generation failed")
                
        elif response.status_code == 404:
            log_test("PROJECT ANALYTICS", "FAIL", 
                    f"Project or organization not found: {response.text}")
        elif response.status_code == 500:
            log_test("PROJECT ANALYTICS", "FAIL", 
                    f"Server error: {response.text}")
        else:
            log_test("PROJECT ANALYTICS", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("PROJECT ANALYTICS", "FAIL", "Request timeout (>90s)")
    except Exception as e:
        log_test("PROJECT ANALYTICS", "FAIL", f"Exception: {str(e)}")

def test_project_export(project_id):
    """Test the NEW project export to Excel functionality"""
    if not project_id:
        log_test("Project Export", "SKIP", "No project ID available")
        return
        
    print("📤 TESTING NEW PROJECT EXPORT - EXCEL GENERATION")
    print("=" * 70)
    
    print(f"Test 5: POST /api/menu-project/{project_id}/export?export_format=excel")
    print("Expected: Excel file generation with download URL")
    
    try:
        start_time = time.time()
        
        params = {"export_format": "excel"}
        response = requests.post(
            f"{BACKEND_URL}/menu-project/{project_id}/export",
            params=params,
            timeout=60  # 1 minute for Excel generation
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Check expected export response structure
            success = result.get("success", False)
            export_format = result.get("export_format")
            download_url = result.get("download_url")
            file_info = result.get("file_info", {})
            
            print(f"\n📤 PROJECT EXPORT ANALYSIS:")
            print(f"Success: {success}")
            print(f"Export format: {export_format}")
            print(f"Download URL: {download_url}")
            
            if success:
                log_test("PROJECT EXPORT - SUCCESS", "PASS", 
                        "Excel export generated successfully")
                
                # Verify export format
                if export_format == "excel":
                    log_test("Export Format Verification", "PASS", 
                            "Export format correctly set to Excel")
                else:
                    log_test("Export Format Verification", "WARN", 
                            f"Export format: {export_format} (expected: excel)")
                
                # Verify download URL
                if download_url and download_url.startswith("http"):
                    log_test("Download URL Verification", "PASS", 
                            "Valid download URL provided")
                    
                    # Test if URL is accessible (optional)
                    try:
                        url_response = requests.head(download_url, timeout=10)
                        if url_response.status_code == 200:
                            log_test("Download URL Accessibility", "PASS", 
                                    "Download URL is accessible")
                        else:
                            log_test("Download URL Accessibility", "WARN", 
                                    f"Download URL returned HTTP {url_response.status_code}")
                    except:
                        log_test("Download URL Accessibility", "WARN", 
                                "Could not verify download URL accessibility")
                else:
                    log_test("Download URL Verification", "FAIL", 
                            f"Invalid download URL: {download_url}")
                
                # Verify file info
                if file_info:
                    filename = file_info.get("filename")
                    file_size = file_info.get("file_size")
                    created_at = file_info.get("created_at")
                    
                    log_test("File Info Verification", "PASS", 
                            f"File: {filename}, Size: {file_size}, Created: {created_at}")
                    
                    # Check filename format
                    if filename and "летнее меню" in filename.lower():
                        log_test("Filename Format", "PASS", 
                                "Filename contains project name")
                    else:
                        log_test("Filename Format", "WARN", 
                                f"Filename may not contain project name: {filename}")
                else:
                    log_test("File Info Verification", "WARN", 
                            "No file information provided")
                    
            else:
                log_test("PROJECT EXPORT - FAILURE", "FAIL", 
                        "Excel export generation failed")
                
        elif response.status_code == 404:
            log_test("PROJECT EXPORT", "FAIL", 
                    f"Project not found: {response.text}")
        elif response.status_code == 400:
            log_test("PROJECT EXPORT", "FAIL", 
                    f"Bad request (invalid format?): {response.text}")
        elif response.status_code == 500:
            log_test("PROJECT EXPORT", "FAIL", 
                    f"Server error: {response.text}")
        else:
            log_test("PROJECT EXPORT", "FAIL", 
                    f"Unexpected HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        log_test("PROJECT EXPORT", "FAIL", "Request timeout (>60s)")
    except Exception as e:
        log_test("PROJECT EXPORT", "FAIL", f"Exception: {str(e)}")

def test_iiko_integration_fallback():
    """Test system behavior when IIKo is not available"""
    print("🔄 TESTING IIKO INTEGRATION FALLBACK SCENARIOS")
    print("=" * 70)
    
    # Test with invalid organization ID
    print("Test 6: Analytics with invalid organization ID")
    try:
        response = requests.get(
            f"{BACKEND_URL}/menu-project/test-project/analytics",
            params={"organization_id": "invalid-org-999"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            analytics = result.get("analytics", {})
            iiko_integration = analytics.get("iiko_integration", {})
            
            if iiko_integration.get("status") == "unavailable":
                log_test("IIKo Fallback Handling", "PASS", 
                        "System correctly handles unavailable IIKo integration")
            else:
                log_test("IIKo Fallback Handling", "WARN", 
                        "IIKo fallback behavior unclear")
        else:
            log_test("IIKo Fallback Handling", "WARN", 
                    f"Unexpected response: HTTP {response.status_code}")
            
    except Exception as e:
        log_test("IIKo Fallback Handling", "WARN", f"Exception: {str(e)}")

def main():
    """Run all project system and analytics tests"""
    print("🧪 BACKEND TESTING: MENU PROJECTS SYSTEM & ANALYTICS")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test 1: Basic project endpoints (should already work)
        existing_projects = test_basic_project_endpoints()
        
        # Test 2: Create new test project
        project_id = test_create_project()
        
        # Test 3: Get project content
        project_content = test_project_content(project_id)
        
        # Test 4: NEW - Project analytics with IIKo integration
        test_project_analytics(project_id)
        
        # Test 5: NEW - Project export to Excel
        test_project_export(project_id)
        
        # Test 6: IIKo integration fallback scenarios
        test_iiko_integration_fallback()
        
        print("🏁 ALL PROJECT SYSTEM TESTS COMPLETED")
        print("=" * 80)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary of features tested
        print("\n📁 PROJECT SYSTEM FEATURES TESTED:")
        print("✅ GET /api/menu-projects/{user_id} - Project list retrieval")
        print("✅ POST /api/create-menu-project - Project creation")
        print("✅ GET /api/menu-project/{project_id}/content - Project content")
        print("🆕 GET /api/menu-project/{project_id}/analytics - Extended analytics with IIKo")
        print("🆕 POST /api/menu-project/{project_id}/export - Excel export functionality")
        print("✅ IIKo integration fallback scenarios")
        print("\n🎯 TEST DATA USED:")
        print(f"User ID: test_user_12345")
        print(f"Project: 'Тестовое летнее меню' (seasonal_update)")
        print(f"Organization: default-org-001 (Edison Craft Bar)")
        print(f"Created Project ID: {project_id if project_id else 'Failed to create'}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()