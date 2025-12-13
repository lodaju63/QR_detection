pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
        maven {
            url = uri("https://chaquo.com/maven")
        }
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven {
            url = uri("https://chaquo.com/maven")
        }
        // ✅ [수정] Dynamsoft 전용 저장소 2개 모두 추가 (순서 중요)
        maven { url = uri("https://download2.dynamsoft.com/maven/dbr/aar") }
        maven { url = uri("https://download2.dynamsoft.com/maven/aar") }
    }
}

rootProject.name = "QRScanner"
include(":app")
