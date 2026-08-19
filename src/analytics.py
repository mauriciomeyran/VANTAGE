"""Analytics for VANTAGE Scout, integrated with Layer_1 source_analytics patterns."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class ScoutAnalytics:
    """Analytics system following Layer_1 source_analytics patterns."""
    
    def __init__(self, output_dir: Path, history_window_days: int = 30):
        self.output_dir = output_dir
        self.history_window_days = history_window_days
        self.history = self._load_history()
    
    def _load_history(self) -> list[dict[str, Any]]:
        """Load historical Scout outputs for analytics."""
        history = []
        cutoff_date = datetime.now() - timedelta(days=self.history_window_days)
        
        if not self.output_dir.exists():
            return history
        
        for json_file in self.output_dir.glob("vantage_scout_*.json"):
            try:
                # Check file age against history window
                file_mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    continue
                
                data = json.loads(json_file.read_text())
                history.append({
                    "file": json_file.name,
                    "date": file_mtime,
                    "data": data
                })
            except (json.JSONDecodeError, IOError):
                # Skip corrupted files
                continue
        
        # Sort by date descending
        history.sort(key=lambda x: x["date"], reverse=True)
        return history
    
    def generate_source_effectiveness_report(self) -> dict[str, Any]:
        """Generate report on source effectiveness."""
        source_stats = defaultdict(lambda: {
            "total_attempts": 0,
            "successful": 0,
            "failed": 0,
            "items_extracted": 0,
            "avg_items_per_run": 0,
            "last_success": None,
            "last_failure": None
        })
        
        for entry in self.history:
            data = entry["data"]
            wrapper = data.get("prompt_variant", "Unknown")
            items = data.get("items", [])
            audit_log = data.get("audit_log", [])
            
            stats = source_stats[wrapper]
            stats["total_attempts"] += 1
            stats["items_extracted"] += len(items)
            
            # Check for errors in audit log
            has_errors = any(log.get("type") in ["HTTP", "Timeout", "Cloudflare"] 
                           for log in audit_log)
            
            if has_errors:
                stats["failed"] += 1
                stats["last_failure"] = entry["date"].isoformat()
            else:
                stats["successful"] += 1
                stats["last_success"] = entry["date"].isoformat()
        
        # Calculate averages
        for wrapper, stats in source_stats.items():
            if stats["total_attempts"] > 0:
                stats["avg_items_per_run"] = stats["items_extracted"] / stats["total_attempts"]
                stats["success_rate"] = stats["successful"] / stats["total_attempts"]
            else:
                stats["avg_items_per_run"] = 0
                stats["success_rate"] = 0
        
        return dict(source_stats)
    
    def generate_quality_report(self) -> dict[str, Any]:
        """Generate report on data quality and issues."""
        quality_stats = {
            "total_runs": len(self.history),
            "total_items": 0,
            "items_with_errors": 0,
            "items_with_warnings": 0,
            "common_errors": defaultdict(int),
            "common_warnings": defaultdict(int),
            "data_quality_trends": []
        }
        
        for entry in self.history:
            data = entry["data"]
            items = data.get("items", [])
            audit_log = data.get("audit_log", [])
            warnings = data.get("data_quality_warnings", [])
            
            quality_stats["total_items"] += len(items)
            
            # Count errors
            for log_entry in audit_log:
                error_type = log_entry.get("type", "Unknown")
                quality_stats["common_errors"][error_type] += 1
                quality_stats["items_with_errors"] += 1
            
            # Count warnings
            for warning in warnings:
                warning_code = warning.get("code", "Unknown")
                quality_stats["common_warnings"][warning_code] += 1
                quality_stats["items_with_warnings"] += 1
            
            # Track quality trends over time
            quality_stats["data_quality_trends"].append({
                "date": entry["date"].isoformat(),
                "items_count": len(items),
                "error_count": len(audit_log),
                "warning_count": len(warnings)
            })
        
        # Convert defaultdicts to regular dicts
        quality_stats["common_errors"] = dict(quality_stats["common_errors"])
        quality_stats["common_warnings"] = dict(quality_stats["common_warnings"])
        
        return quality_stats
    
    def generate_temporal_analysis(self) -> dict[str, Any]:
        """Generate temporal analysis of Scout performance."""
        if not self.history:
            return {
                "message": "No historical data available",
                "time_range": "None",
                "frequency": "Unknown"
            }
        
        dates = [entry["date"] for entry in self.history]
        
        # Calculate time range
        if len(dates) >= 2:
            time_range = (dates[0] - dates[-1]).days
        else:
            time_range = 0
        
        # Calculate frequency (runs per week)
        if time_range > 0:
            frequency = len(dates) / (time_range / 7)
        else:
            frequency = 0
        
        # Daily item counts
        daily_counts = defaultdict(int)
        for entry in self.history:
            date_str = entry["date"].strftime("%Y-%m-%d")
            daily_counts[date_str] += len(entry["data"].get("items", []))
        
        return {
            "time_range_days": time_range,
            "total_runs": len(dates),
            "runs_per_week": round(frequency, 2),
            "first_run": dates[-1].isoformat() if dates else None,
            "last_run": dates[0].isoformat() if dates else None,
            "daily_item_counts": dict(daily_counts),
            "avg_items_per_run": sum(len(entry["data"].get("items", [])) for entry in self.history) / len(dates) if dates else 0
        }
    
    def generate_recommendations(self) -> list[dict[str, str]]:
        """Generate actionable recommendations based on analytics."""
        recommendations = []
        
        source_report = self.generate_source_effectiveness_report()
        quality_report = self.generate_quality_report()
        
        # Source effectiveness recommendations
        for source, stats in source_report.items():
            if stats["success_rate"] < 0.5:
                recommendations.append({
                    "type": "source_improvement",
                    "priority": "high",
                    "source": source,
                    "issue": f"Low success rate ({stats['success_rate']:.1%})",
                    "recommendation": "Investigate source configuration or increase timeout settings"
                })
            
            if stats["avg_items_per_run"] < 2:
                recommendations.append({
                    "type": "source_optimization",
                    "priority": "medium",
                    "source": source,
                    "issue": f"Low item yield ({stats['avg_items_per_run']:.1f} items/run)",
                    "recommendation": "Review search queries or source selection criteria"
                })
        
        # Quality recommendations
        if quality_report["common_errors"]:
            most_common_error = max(quality_report["common_errors"].items(), 
                                  key=lambda x: x[1])
            recommendations.append({
                "type": "error_resolution",
                "priority": "high",
                "source": "general",
                "issue": f"Most common error: {most_common_error[0]} ({most_common_error[1]} occurrences)",
                "recommendation": "Investigate root cause and implement targeted fix"
            })
        
        if quality_report["items_with_warnings"] / max(quality_report["total_items"], 1) > 0.3:
            recommendations.append({
                "type": "data_quality",
                "priority": "medium",
                "source": "general",
                "issue": "High rate of data quality warnings",
                "recommendation": "Review validation rules and source data quality"
            })
        
        return recommendations
    
    def generate_comprehensive_report(self) -> dict[str, Any]:
        """Generate comprehensive analytics report."""
        return {
            "generated_at": datetime.now().isoformat(),
            "history_window_days": self.history_window_days,
            "total_runs_analyzed": len(self.history),
            "source_effectiveness": self.generate_source_effectiveness_report(),
            "data_quality": self.generate_quality_report(),
            "temporal_analysis": self.generate_temporal_analysis(),
            "recommendations": self.generate_recommendations()
        }