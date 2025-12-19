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
        // ✅ [수정] Dynamsoft Maven 저장소
        maven { url = uri("https://download2.dynamsoft.com/maven/aar") }
    }
}

rootProject.name = "QRScanner"
include(":app")



