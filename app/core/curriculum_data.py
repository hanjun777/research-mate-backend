# Static data for curriculum

SUBJECTS = ["수학"]

# Example data structure for units. 
# This should be expanded based on actual high school curriculum.
# Using a simplified version for demonstration as per spec example.

UNITS = {
    "수학": [
        {
            "unit_large": "미적분",
            "children": [
                 # This structure is not fully defined in spec, so we infer "Medium > Small" or just list of medium?
                 # Spec says: children: [ ... ]
                 # Spec example in recommendation body says: unit_large, unit_medium, unit_small.
                 # So hierarchy is Large -> Medium -> Small.
                 {
                     "unit_medium": "수열의 극한",
                     "children": ["수열의 극한", "급수"]
                 },
                 {
                     "unit_medium": "미분법",
                     "children": ["여러 가지 함수의 미분", "도함수의 활용"]
                 }
            ]
        },
        {
            "unit_large": "기하",
            "children": [
                {
                    "unit_medium": "이차곡선",
                    "children": ["포물선", "타원", "쌍곡선"]
                }
            ]
        }
    ],
    # 이후 과목 확장은 DB 기반으로 대체 예정
}
