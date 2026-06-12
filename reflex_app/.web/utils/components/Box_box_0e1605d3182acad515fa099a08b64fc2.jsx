
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_0e1605d3182acad515fa099a08b64fc2 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_a9859c41d5dc1bb39fc8e1a860c406d9 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.export_transactions_csv", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "11px", ["letterSpacing"] : "0.08em", ["padding"] : "8px 12px", ["borderRadius"] : "8px", ["border"] : "1px solid #252535", ["color"] : "#8282a2", ["cursor"] : "pointer", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["&:hover"] : ({ ["background"] : "#14141c", ["color"] : "#f0f0fa" }) }),onClick:on_click_a9859c41d5dc1bb39fc8e1a860c406d9},children)
    )
});
