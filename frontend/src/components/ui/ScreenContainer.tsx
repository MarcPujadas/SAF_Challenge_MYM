import { useEffect, useRef } from 'react';
import type { ReactNode, Ref } from 'react';
import { Animated, ScrollView, StyleSheet, View } from 'react-native';
import type { ScrollViewInstance, StyleProp, ViewStyle } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { colors, spacing } from '../../theme/theme';

type Props = {
  children: ReactNode;
  scroll?: boolean; // per defecte amb scroll
  scrollRef?: Ref<ScrollViewInstance>;
  contentStyle?: StyleProp<ViewStyle>;
  // Espai extra al final (p. ex. alcada de la targeta flotant de SAFi).
  bottomPadding?: number;
};

// Fons de pantalla + arees segures + fade-in curt. El header superior el gestiona la navegacio.
export default function ScreenContainer({
  children,
  scroll = true,
  scrollRef,
  contentStyle,
  bottomPadding = 0,
}: Props) {
  const insets = useSafeAreaInsets();
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(opacity, { toValue: 1, duration: 180, useNativeDriver: true }).start();
  }, [opacity]);

  const padding = {
    paddingHorizontal: spacing.lg + Math.max(insets.left, insets.right, 0),
    paddingTop: spacing.lg,
    paddingBottom: spacing.xxl + insets.bottom + bottomPadding,
  };

  return (
    <Animated.View style={[styles.root, { opacity }]}>
      {scroll ? (
        <ScrollView
          ref={scrollRef}
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={[padding, contentStyle]}
        >
          {children}
        </ScrollView>
      ) : (
        <View style={[styles.flex, padding, contentStyle]}>{children}</View>
      )}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.background },
  flex: { flex: 1 },
});
