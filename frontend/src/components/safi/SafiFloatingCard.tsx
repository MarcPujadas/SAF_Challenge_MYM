import { useEffect, useRef, useState } from 'react';
import {
  Animated,
  PanResponder,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Button } from '../ui';
import { MIN_TOUCH, colors, radius, shadow, spacing } from '../../theme/theme';

// Notificacio flotant de SAFi: fixa a baix (fora del scroll), compacta per defecte i ampliable
// arrossegant la nansa/capcalera. Nomes presentacio: les dades i les accions les decideix la pantalla.

type Props = {
  title?: string;
  message: string;
  // Accio opcional (p. ex. "Canviar a 19:45"). La logica (accepted/ignored) viu a la pantalla.
  actionLabel?: string;
  onAction?: () => void;
  actionDisabled?: boolean;
  onDismiss: () => void;
  // Alcada actualment ocupada a baix de la pantalla (targeta visible + marges + safe area).
  onHeightChange?: (height: number) => void;
};

const SIDE_MARGIN = spacing.md;
const BOTTOM_MARGIN = spacing.sm;

export default function SafiFloatingCard({
  title = 'SAFi',
  message,
  actionLabel,
  onAction,
  actionDisabled,
  onDismiss,
  onHeightChange,
}: Props) {
  const insets = useSafeAreaInsets();
  const { height: screenH } = useWindowDimensions();
  const maxH = screenH * 0.55;

  const [headerH, setHeaderH] = useState(0);
  const [cardH, setCardH] = useState(0);
  const [expanded, setExpanded] = useState(false);
  const expandedRef = useRef(false);

  // Distancia entre estat ampliat i compacte (px).
  const collapse = Math.max(cardH - headerH, 0);
  const collapseRef = useRef(0);
  collapseRef.current = collapse;

  const ty = useRef(new Animated.Value(0)).current;
  const fade = useRef(new Animated.Value(0)).current;
  const ready = headerH > 0 && cardH > 0;

  function snapTo(open: boolean) {
    expandedRef.current = open;
    setExpanded(open);
    Animated.spring(ty, {
      toValue: open ? 0 : collapseRef.current,
      useNativeDriver: true,
      bounciness: 4,
      speed: 14,
    }).start();
  }

  // Quan canvia la mida (missatge nou) i esta compacta, es recol·loca sense animar.
  useEffect(() => {
    if (!expandedRef.current) ty.setValue(collapse);
  }, [collapse, ty]);

  useEffect(() => {
    if (ready) Animated.timing(fade, { toValue: 1, duration: 180, useNativeDriver: true }).start();
  }, [ready, fade]);

  useEffect(() => {
    if (!ready) return;
    onHeightChange?.((expanded ? cardH : headerH) + insets.bottom + BOTTOM_MARGIN);
  }, [ready, expanded, cardH, headerH, insets.bottom, onHeightChange]);

  // Arrossegament vertical nomes a la nansa/capcalera (el cos fa scroll pel seu compte).
  const pan = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dy) > 6 && Math.abs(g.dy) > Math.abs(g.dx),
      onPanResponderMove: (_, g) => {
        const base = expandedRef.current ? 0 : collapseRef.current;
        ty.setValue(Math.min(Math.max(base + g.dy, 0), collapseRef.current));
      },
      onPanResponderRelease: (_, g) => {
        if (g.dy < -30 || g.vy < -0.5) snapTo(true);
        else if (g.dy > 30 || g.vy > 0.5) snapTo(false);
        else snapTo(expandedRef.current);
      },
      onPanResponderTerminate: () => snapTo(expandedRef.current),
    }),
  ).current;

  const bodyOpacity = ty.interpolate({
    inputRange: [0, Math.max(collapse, 1)],
    outputRange: [1, 0],
    extrapolate: 'clamp',
  });

  return (
    <Animated.View
      pointerEvents="box-none"
      onLayout={(e) => setCardH(e.nativeEvent.layout.height)}
      style={[
        styles.wrap,
        {
          left: SIDE_MARGIN + insets.left,
          right: SIDE_MARGIN + insets.right,
          bottom: insets.bottom + BOTTOM_MARGIN,
          maxHeight: maxH,
          opacity: fade,
          transform: [{ translateY: ty }],
        },
      ]}
    >
      {/* Capcalera = nansa: arrossegable; icona + missatge d'una linia + fletxa + creu */}
      <View
        {...pan.panHandlers}
        onLayout={(e) => setHeaderH(e.nativeEvent.layout.height)}
        style={styles.header}
      >
        <View style={styles.grip} />
        <View style={styles.headerRow}>
          <Pressable
            style={styles.headerMain}
            accessibilityRole="button"
            accessibilityLabel={expanded ? 'Reduir la recomanació de SAFi' : 'Ampliar la recomanació de SAFi'}
            onPress={() => snapTo(!expandedRef.current)}
          >
            <View style={styles.icon}>
              <Text style={styles.iconText}>✨</Text>
            </View>
            <Text style={styles.compactText} numberOfLines={1} ellipsizeMode="tail">
              {message}
            </Text>
          </Pressable>
          <Pressable
            style={styles.iconButton}
            accessibilityRole="button"
            accessibilityLabel={expanded ? 'Reduir la targeta de SAFi' : 'Ampliar la targeta de SAFi'}
            onPress={() => snapTo(!expandedRef.current)}
          >
            <Text style={styles.arrow}>{expanded ? '▼' : '▲'}</Text>
          </Pressable>
          <Pressable
            style={styles.iconButton}
            accessibilityRole="button"
            accessibilityLabel="Descartar la recomanació de SAFi"
            onPress={onDismiss}
          >
            <Text style={styles.close}>✕</Text>
          </Pressable>
        </View>
      </View>

      {/* Cos: recomanacio completa; invisible i no interactiu quan esta compacta */}
      <Animated.View
        pointerEvents={expanded ? 'auto' : 'none'}
        style={[styles.body, { opacity: bodyOpacity }]}
      >
        <ScrollView nestedScrollEnabled showsVerticalScrollIndicator={false}>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.fullText}>{message}</Text>
          {actionLabel && onAction ? (
            <Button
              label={actionLabel}
              onPress={onAction}
              disabled={actionDisabled}
              style={styles.action}
            />
          ) : null}
        </ScrollView>
      </Animated.View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  wrap: { position: 'absolute' },
  header: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: colors.safi,
    paddingTop: spacing.xs,
    paddingHorizontal: spacing.sm,
    zIndex: 2,
    ...shadow.floating,
  },
  grip: {
    alignSelf: 'center',
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.border,
    marginBottom: 2,
  },
  headerRow: { flexDirection: 'row', alignItems: 'center' },
  headerMain: { flex: 1, minHeight: MIN_TOUCH, flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  icon: {
    width: 32,
    height: 32,
    borderRadius: radius.pill,
    backgroundColor: colors.safiSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconText: { fontSize: 16 },
  compactText: { flex: 1, fontSize: 14, fontWeight: '600', color: colors.text },
  iconButton: { width: MIN_TOUCH, height: MIN_TOUCH, alignItems: 'center', justifyContent: 'center' },
  arrow: { fontSize: 14, color: colors.safi },
  close: { fontSize: 18, color: colors.textMuted },
  body: {
    marginTop: -radius.xl,
    paddingTop: radius.xl + spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.lg,
    backgroundColor: colors.surface,
    borderBottomLeftRadius: radius.xl,
    borderBottomRightRadius: radius.xl,
    borderWidth: 1,
    borderTopWidth: 0,
    borderColor: colors.safi,
    flexShrink: 1,
  },
  title: { fontSize: 13, fontWeight: '800', color: colors.safi, marginBottom: spacing.xs },
  fullText: { fontSize: 16, color: colors.text },
  action: { marginTop: spacing.md },
});
