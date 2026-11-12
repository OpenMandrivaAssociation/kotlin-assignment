Name:		kotlin-assignment
Version:	2.4.21
Release:	1
Summary:	Kotlin assignment compiler plugin Gradle support
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/JetBrains/kotlin
# Kotlin tag v2.4.21. Gradle subplugin compiled with kotlinc 2.0.21.
# Compiler plugin classes stay out of this jar.
Source0:	kotlin-assignment-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-21-openjdk-devel
BuildRequires:	kotlin
BuildRequires:	gradle
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-stdlib)
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-gradle-plugin-api)
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-gradle-plugin-annotations)
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-tooling-core)
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-build-tools-api)

%description
org.jetbrains.kotlin:kotlin-assignment %{version}.
Gradle subplugin that registers assignment annotations for the Kotlin assignment compiler plugin.

%prep
%autosetup -n kotlin-assignment-%{version}
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
CPG=$(find /usr/share/gradle/lib -name '*.jar' | sort | paste -sd: -)
test -n "$CPG"
CPSTD=%{_javadir}/kotlin-stdlib.jar
CPAPI=%{_javadir}/kotlin-gradle-plugin-api.jar
CPANN=%{_javadir}/kotlin-gradle-plugin-annotations.jar
CPTOOL=%{_javadir}/kotlin-tooling-core.jar
CPBTA=%{_javadir}/kotlin-build-tools-api.jar
test -s "$CPSTD"
test -s "$CPAPI"
test -s "$CPANN"
test -s "$CPTOOL"
test -s "$CPBTA"
mkdir -p classes
find src -name '*.kt' | sort > sources.list
test "$(wc -l < sources.list)" -eq 2
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 -no-stdlib \
	-module-name kotlin.assignment \
	-cp "$CPG:$CPSTD:$CPAPI:$CPANN:$CPTOOL:$CPBTA" \
	-d classes @sources.list
mkdir -p classes/META-INF
cp -a resources/META-INF/gradle-plugins classes/META-INF/
cp -a resources/META-INF/services classes/META-INF/
test -s classes/META-INF/gradle-plugins/kotlin-value-container-assignment.properties
grep -F -qx 'org.jetbrains.kotlin.assignment.plugin.gradle.AssignmentSubplugin' classes/META-INF/services/org.jetbrains.kotlin.gradle.plugin.KotlinGradleSubplugin
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: kotlin.assignment' > manifest.mf
jar cfm kotlin-assignment.jar manifest.mf -C classes .
jar i kotlin-assignment.jar
desc=$(jar --describe-module --file kotlin-assignment.jar)
printf '%s\n' "$desc"
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi
printf '%s\n' "$desc" | grep -F -qx 'kotlin.assignment automatic'
jar tf kotlin-assignment.jar | grep -F -qx 'META-INF/gradle-plugins/kotlin-value-container-assignment.properties'
cat > kotlin-assignment.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.jetbrains.kotlin</groupId>
  <artifactId>kotlin-assignment</artifactId>
  <version>%{version}</version>
  <name>kotlin-assignment</name>
  <description>Kotlin assignment compiler plugin Gradle support</description>
  <url>https://github.com/JetBrains/kotlin</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-stdlib</artifactId>
      <version>2.0.21</version>
    </dependency>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-gradle-plugin-api</artifactId>
      <version>2.4.21</version>
    </dependency>
  </dependencies>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact kotlin-assignment.pom:kotlin-assignment.jar \
	--file-name kotlin-assignment \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/org.jetbrains.kotlin/kotlin-assignment.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "kotlin-assignment"' "$idx"
test -s %{buildroot}%{_javadir}/kotlin-assignment.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
JAR=%{buildroot}%{_javadir}/kotlin-assignment.jar
test -s "$JAR"
STDLIB=%{_javadir}/kotlin-stdlib.jar
API=%{_javadir}/kotlin-gradle-plugin-api.jar
TOOL=%{_javadir}/kotlin-tooling-core.jar
CPG=$(find /usr/share/gradle/lib -name '*.jar' | sort | paste -sd: -)
test -n "$CPG"
mkdir -p check
cat > check/Probe.kt << 'EOF'
import org.jetbrains.kotlin.assignment.plugin.gradle.AssignmentExtension
import org.jetbrains.kotlin.gradle.plugin.KotlinCompilerPluginSupportPlugin

fun main() {
    val ext = AssignmentExtension()
    ext.annotation("gradle")
    ext.annotations("a", "b")
    if (ext.myAnnotations != listOf("gradle", "a", "b")) error(ext.myAnnotations.toString())
    val type = Class.forName("org.jetbrains.kotlin.assignment.plugin.gradle.AssignmentSubplugin")
    if (!KotlinCompilerPluginSupportPlugin::class.java.isAssignableFrom(type)) error("plugin")
    println("kotlin_assignment_ok " + ext.myAnnotations.size)
}
EOF
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 -no-stdlib \
	-Xfriend-paths="$JAR" \
	-cp "$JAR:$STDLIB:$API:$TOOL:$CPG" -d check/out check/Probe.kt
java -cp "check/out:$JAR:$STDLIB:$API:$TOOL:$CPG" ProbeKt > check/out.txt
cat check/out.txt
grep -F -qx 'kotlin_assignment_ok 3' check/out.txt

%files -f .mfiles
%license LICENSE.txt
%doc NOTICE.txt
