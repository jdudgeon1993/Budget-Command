
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_3f8580da012ab213fcfff97e6a4fa218 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_a9859c41d5dc1bb39fc8e1a860c406d9 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.export_transactions_csv", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "11px", ["letterSpacing"] : "0.08em", ["padding"] : "8px 12px", ["borderRadius"] : "8px", ["border"] : "1px solid rgba(255,255,255,0.08)", ["color"] : "#9090B8", ["cursor"] : "pointer", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["&:hover"] : ({ ["background"] : "rgba(255,255,255,0.05)", ["color"] : "#FFFFFF" }) }),onClick:on_click_a9859c41d5dc1bb39fc8e1a860c406d9},children)
    )
});
